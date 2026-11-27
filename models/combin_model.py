import pandas as pd
import numpy as np
import os
import random

items_df = None
rules_df = None

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(MODEL_DIR, 'data')

# Renk ve Kategori Tanımları
KNOWN_COLORS = [
    "siyah", "beyaz", "kırmızı", "mavi", "yeşil", "sarı", "mor", 
    "pembe", "turuncu", "gri", "kahverengi", "lacivert", "bej", 
    "bordo", "haki", "turkuaz", "lila", "krem", "gümüş", "altın"
]

KNOWN_CATEGORIES = [
    "pantolon", "etek", "elbise", "tişört", "gömlek", "kazak", 
    "bluz", "ceket", "mont", "kaban", "ayakkabı", "bot", 
    "çizme", "çanta", "şort", "tulum", "yelek", "hırka"
]

def load_combin_model():
    global items_df, rules_df
    if items_df is not None: return

    try:
        items_df = pd.read_csv(os.path.join(DATA_DIR, 'items_processed.csv'))
        items_df['name'] = items_df['name'].astype(str)
        items_df['category'] = items_df['category'].astype(str)
        items_df['color'] = items_df['color'].astype(str)
        rules_df = pd.read_csv(os.path.join(DATA_DIR, 'outfit_cooccurrence_rules.csv'))
        # Başarılı yükleme mesajını kapattık, app.py zaten genel bilgi veriyor
    except Exception as e:
        print(f"❌ Model Yükleme Hatası: {e}")

def search_products(query_text):
    global items_df
    if items_df is None: return pd.DataFrame()
    if not query_text: return items_df.head(20)

    query_text = query_text.lower().strip()
    words = query_text.split()
    detected_color = None
    detected_category = None
    other_keywords = []

    for word in words:
        if word in KNOWN_COLORS: detected_color = word
        elif word in KNOWN_CATEGORIES: detected_category = word
        else: other_keywords.append(word)

    filtered_df = items_df.copy()
    if detected_category:
        filtered_df = filtered_df[filtered_df['category'].str.contains(detected_category, case=False, na=False)]
    if detected_color:
        filtered_df = filtered_df[filtered_df['color'].str.contains(detected_color, case=False, na=False)]
    if other_keywords:
        keyword_search = " ".join(other_keywords)
        filtered_df = filtered_df[filtered_df['name'].str.contains(keyword_search, case=False, na=False)]

    return filtered_df

def color_compatibility_score(color1, color2):
    if str(color1) == str(color2): return 10.0
    if color1 == 'karışık' or color2 == 'karışık': return 7.0
    
    COMPATIBILITY = {
        'pembe': {'beyaz': 9, 'gri': 8, 'siyah': 7, 'mor': 8, 'kırmızı': 6, 'bej': 7, 'pembe': 10},
        'siyah': {'beyaz': 10, 'gri': 9, 'kırmızı': 8, 'pembe': 7, 'mavi': 7, 'mor': 7, 'siyah': 10},
        'beyaz': {'siyah': 10, 'gri': 9, 'mavi': 9, 'lacivert': 8, 'pembe': 9, 'kırmızı': 8, 'kahverengi': 7, 'bej': 9, 'mor': 9, 'beyaz': 10},
        'mavi': {'beyaz': 9, 'gri': 8, 'lacivert': 9, 'siyah': 7, 'kahverengi': 6, 'mavi': 10},
        'kırmızı': {'siyah': 8, 'beyaz': 8, 'pembe': 6, 'bordo': 7, 'gri': 6, 'kırmızı': 10},
        'gri': {'siyah': 9, 'beyaz': 9, 'mavi': 8, 'pembe': 8, 'mor': 7, 'kırmızı': 6, 'lacivert': 7, 'gri': 10},
        'kahverengi': {'bej': 9, 'turuncu': 7, 'yeşil': 7, 'beyaz': 7, 'mavi': 6, 'kahverengi': 10},
        'yeşil': {'kahverengi': 7, 'siyah': 6, 'beyaz': 7, 'bej': 6, 'yeşil': 10},
        'sarı': {'turuncu': 8, 'beyaz': 7, 'kahverengi': 6, 'sarı': 10},
        'mor': {'siyah': 8, 'beyaz': 9, 'pembe': 8, 'gri': 7, 'mor': 10, 'lila': 9},
        'lacivert': {'beyaz': 9, 'gri': 8, 'mavi': 9, 'siyah': 7, 'lacivert': 10},
        'bej': {'kahverengi': 9, 'beyaz': 9, 'pembe': 7, 'yeşil': 6, 'bej': 10}
    }
    
    c1, c2 = str(color1).lower(), str(color2).lower()
    if c1 in COMPATIBILITY and c2 in COMPATIBILITY[c1]: return float(COMPATIBILITY[c1][c2])
    if c2 in COMPATIBILITY and c1 in COMPATIBILITY[c2]: return float(COMPATIBILITY[c2][c1])
    return 3.0

def get_combin_recommendations(item_id, top_k=8, enforce_season=None, source_category=None):
    global items_df, rules_df
    if items_df is None or rules_df is None: return pd.DataFrame()
    
    try:
        source_item = items_df[items_df['item_id'] == item_id]
        if len(source_item) == 0: return pd.DataFrame()
        
        source_item = source_item.iloc[0]
        source_cat = str(source_category or source_item['category']).lower()
        source_season = enforce_season or source_item['season']
        source_color = source_item['color']
        
        # Gereksiz detay logu kaldırıldı

        COMPLEMENTARY = {
            'pantolon': ['tişört', 'gömlek', 'kazak', 'bluz', 'ceket', 'mont', 'ayakkabı', 'çanta'],
            'etek': ['tişört', 'gömlek', 'kazak', 'bluz', 'ceket', 'mont', 'ayakkabı', 'çizme', 'çanta'],
            'şort': ['tişört', 'gömlek', 'bluz', 'ayakkabı', 'çanta'],
            'tişört': ['pantolon', 'etek', 'şort', 'ayakkabı', 'ceket', 'gömlek', 'çanta'],
            'gömlek': ['pantolon', 'etek', 'şort', 'ceket', 'ayakkabı', 'çanta'],
            'kazak': ['pantolon', 'etek', 'mont', 'ayakkabı', 'çanta'],
            'bluz': ['pantolon', 'etek', 'ceket', 'ayakkabı'],
            'elbise': ['ayakkabı', 'çanta', 'ceket', 'mont', 'takı'],
            'ayakkabı': ['pantolon', 'etek', 'elbise', 'şort', 'tişört', 'gömlek', 'çanta'],
            'mont': ['pantolon', 'etek', 'elbise', 'tişört', 'kazak', 'ayakkabı', 'bot'],
            'ceket': ['pantolon', 'etek', 'elbise', 'tişört', 'gömlek', 'ayakkabı'],
            'çanta': ['elbise', 'pantolon', 'etek', 'tişört', 'ayakkabı', 'mont']
        }
        
        target_categories = COMPLEMENTARY.get(source_cat, [])
        if not target_categories: target_categories = ['pantolon', 'tişört', 'ayakkabı']

        scored_recommendations = []
        
        # 1. CO-OCCURRENCE
        product_rules = rules_df[(rules_df['antecedent'] == item_id) | (rules_df['consequent'] == item_id)].copy()
        if len(product_rules) > 0:
            product_rules = product_rules.sort_values('cooccurrence_count', ascending=False)
            for _, rule in product_rules.iterrows():
                related_id = rule['consequent'] if rule['antecedent'] == item_id else rule['antecedent']
                related = items_df[items_df['item_id'] == related_id]
                if len(related) > 0:
                    item = related.iloc[0]
                    if str(item['category']).lower() == source_cat: continue
                    if (source_season == 'yaz' and item['season'] == 'kış') or \
                       (source_season == 'kış' and item['season'] == 'yaz'): continue

                    c_score = color_compatibility_score(source_color, item['color'])
                    score = (min(10, rule['cooccurrence_count']/5) * 5) + (c_score * 2)
                    scored_recommendations.append({
                        'item_id': item['item_id'], 'name': item['name'], 'category': item['category'], 
                        'color': item['color'], 'season': item['season'], 'image': item['image'],
                        'score': score, 'reason': 'Birlikte Alınan'
                    })

        # 2. FALLBACK STRATEGIES
        MIN_ITEMS_PER_CAT = 8
        for target_cat in target_categories:
            current_count = sum(1 for r in scored_recommendations if target_cat in str(r['category']).lower())
            if current_count >= MIN_ITEMS_PER_CAT: continue
            needed = MIN_ITEMS_PER_CAT - current_count
            
            strategies = [
                {'season_match': True, 'min_color': 6.0, 'score_boost': 20, 'reason': 'Mükemmel Uyum'},
                {'season_match': True, 'min_color': 4.0, 'score_boost': 15, 'reason': 'Mevsim Uyumu'},
                {'season_match': True, 'min_color': 0.0, 'score_boost': 10, 'reason': 'Sezon Önerisi'},
                {'season_match': False, 'min_color': 0.0, 'score_boost': 5, 'reason': 'Alternatif'}
            ]
            
            for strategy in strategies:
                if needed <= 0: break
                candidates = items_df[(items_df['category'].str.contains(target_cat, case=False, na=False)) & (items_df['category'] != source_cat)]
                if strategy['season_match']:
                    candidates = candidates[(candidates['season'] == source_season) | (candidates['season'] == 'dört mevsim')]
                else:
                    if source_season == 'yaz': candidates = candidates[candidates['season'] != 'kış']
                    elif source_season == 'kış': candidates = candidates[candidates['season'] != 'yaz']
                
                if len(candidates) > 0: candidates = candidates.sample(frac=1).reset_index(drop=True)
                
                for _, item in candidates.iterrows():
                    if needed <= 0: break
                    if any(r['item_id'] == item['item_id'] for r in scored_recommendations): continue
                    c_score = color_compatibility_score(source_color, item['color'])
                    if c_score < strategy['min_color']: continue
                    
                    final_score = c_score * 2 + strategy['score_boost']
                    scored_recommendations.append({
                        'item_id': item['item_id'], 'name': item['name'], 'category': item['category'], 
                        'color': item['color'], 'season': item['season'], 'image': item['image'],
                        'score': final_score, 'reason': strategy['reason']
                    })
                    needed -= 1
                    current_count += 1

        scored_recommendations = sorted(scored_recommendations, key=lambda x: x['score'], reverse=True)
        if scored_recommendations:
            max_s = max(r['score'] for r in scored_recommendations)
            for r in scored_recommendations:
                r['score'] = (r['score'] / max_s * 10) if max_s > 0 else 5.0

        return pd.DataFrame(scored_recommendations)

    except Exception as e:
        print(f"❌ Kombin Hatası: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    load_combin_model()
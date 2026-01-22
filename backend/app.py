from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os
import pandas as pd
import time
import json
import random
from dotenv import load_dotenv
from gemini_tryon import GeminiTryOnGenerator

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'models'))
sys.path.insert(0, MODELS_DIR)

DATASET_IMAGES_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend', 'public', 'images'))
GENERATED_DIR = os.path.join(BASE_DIR, 'static', 'generated')
os.makedirs(GENERATED_DIR, exist_ok=True)
BASE_MODEL_PATH = os.path.join(BASE_DIR, 'static', 'models', 'base_model.jpg')

# API KEY GÜVENLİK KONTROLÜ
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("🚨 HATA: .env dosyası bulunamadı veya API Key eksik!")

# --- VERİ YÜKLEME ---
items_df = None
POOL_TOPS = []
POOL_BOTTOMS = []
POOL_SHOES = []
# Montları ayrı tutuyoruz ki etek üstüne mont önermesin
POOL_OUTERWEAR = [] 

def determine_detailed_category(cat_name):
    """
    Ürünleri kategorize ederken senin orijinal geniş listeni kullanıyoruz.
    Böylece hiçbir ayakkabı dışarıda kalmayacak.
    """
    cat = str(cat_name).lower()
    
    # 1. DIŞ GİYİM (Montlar)
    outerwear_keys = ['mont', 'kaban', 'ceket', 'jacket', 'coat', 'blazer', 'yelek', 'vest', 'hırka', 'cardigan', 'kimono', 'poncho', 'outerwear']
    if any(k in cat for k in outerwear_keys): return 'outerwear'

    # 2. ÜST GİYİM
    top_keys = ['tişört', 'gömlek', 'kazak', 'bluz', 'top', 'shirt', 'sweater', 'crop', 'bustier', 'hoodie', 'sweatshirt', 't-shirt', 'tank', 'body', 'tunic', 'polo', 'knitwear', 'süveter']
    if any(k in cat for k in top_keys): return 'top'

    # 3. ALT GİYİM
    bottom_keys = ['pantolon', 'etek', 'şort', 'jean', 'tayt', 'skirt', 'shorts', 'trousers', 'pants', 'denim', 'leggings', 'joggers', 'tulum', 'jumpsuit', 'salopet', 'bottom']
    if any(k in cat for k in bottom_keys): return 'bottom'

    # 4. AYAKKABI & ÇANTA (Senin orijinal geniş listen)
    # Bu liste sayesinde havuzun dolması garanti altına alınıyor.
    shoe_keys = [
        'ayakkabı', 'bot', 'çizme', 'shoes', 'boots', 'heels', 'sandalet', 'terlik', 
        'sneakers', 'sandals', 'flat', 'pump', 'loafer', 'wedge', 'platform', 
        'babet', 'stiletto', 'footwear', 'ankle', 'espadrille', 'mule', 'slipper',
        'çanta', 'bag', 'handbag', 'purse', 'clutch', 'takı', 'accessories'
    ]
    if any(k in cat for k in shoe_keys): return 'shoes'
    
    return 'other'

def load_data():
    global items_df, POOL_TOPS, POOL_BOTTOMS, POOL_SHOES, POOL_OUTERWEAR
    print("--- [SİSTEM] Başlatılıyor... ---")
    
    try:
        from combin_model import load_combin_model
        load_combin_model()
    except ImportError:
        print("⚠️ Uyarı: Combin Modeli yüklenemedi.")

    csv_path = os.path.join(MODELS_DIR, 'data', 'items_processed.csv')
    
    if os.path.exists(csv_path):
        items_df = pd.read_csv(csv_path)
        items_df['image'] = items_df['image'].apply(lambda x: os.path.basename(str(x)) if pd.notnull(x) else x)
        items_df['name'] = items_df['name'].fillna('').astype(str).str.lower()
        items_df['category'] = items_df['category'].fillna('').astype(str).str.lower()
        items_df['color'] = items_df['color'].fillna('').astype(str).str.lower()
        items_df['item_id'] = items_df['item_id'].astype(str)
        
        # Havuzları Sıfırla
        POOL_TOPS = []
        POOL_BOTTOMS = []
        POOL_SHOES = []
        POOL_OUTERWEAR = []
        
        # Havuzları Doldur
        for _, row in items_df.iterrows():
            item = row.to_dict()
            if 'image' in item and item['image']:
                if not str(item['image']).startswith('/images/'):
                    item['image'] = f"/images/{os.path.basename(str(item['image']))}"
            
            # Kategori belirle
            group = determine_detailed_category(item['category'])
            
            if group == 'top': POOL_TOPS.append(item)
            elif group == 'bottom': POOL_BOTTOMS.append(item)
            elif group == 'shoes': POOL_SHOES.append(item)
            elif group == 'outerwear': POOL_OUTERWEAR.append(item)
            
        print(f"📊 HAVUZ DURUMU: Üst: {len(POOL_TOPS)}, Alt: {len(POOL_BOTTOMS)}, Dış: {len(POOL_OUTERWEAR)}, Ayakkabı: {len(POOL_SHOES)}")
        print(f"✅ Sistem Hazır! Toplam {len(items_df)} ürün yüklendi.")
    else:
        print("❌ KRİTİK HATA: Veri dosyası (CSV) bulunamadı!")

load_data()

try:
    try_on_engine = GeminiTryOnGenerator(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"❌ Gemini Başlatma Hatası: {e}")
    try_on_engine = None

# --- ARAMA MANTIĞI (Düzeltilmiş Hali) ---
CATEGORY_MAP = {
    'etek': ['skirt', 'midi skirt', 'mini skirt', 'maxi skirt'],
    'şort': ['shorts', 'denim shorts', 'bermuda'],
    'pantolon': ['trousers', 'pants', 'jeans', 'leggings', 'joggers', 'denim'],
    'elbise': ['dress', 'gown', 'sundress'],
    'tişört': ['t-shirt', 'tee', 'top', 'crop top'],
    'gömlek': ['shirt', 'blouse'],
    'kazak': ['sweater', 'cardigan', 'jumper'],
    'mont': ['coat', 'jacket', 'blazer'],
    'ayakkabı': ['shoes', 'heels', 'boots', 'sneakers'],
    'çanta': ['bag', 'handbag', 'purse']
}

COLOR_FAMILIES = {
    'mavi': ['blue', 'navy', 'teal', 'azure', 'indigo'], 
    'kırmızı': ['red', 'maroon', 'crimson'], 
    'yeşil': ['green', 'olive', 'emerald'], 
    'sarı': ['yellow', 'gold'],
    'pembe': ['pink', 'rose', 'fuchsia'], 
    'mor': ['purple', 'violet', 'lavender'],
    'beyaz': ['white', 'cream'], 
    'siyah': ['black'], 
    'gri': ['grey', 'gray']
}

def strict_business_search(query):
    if not query: return []
    if items_df is None: return []

    query_lower = query.lower()
    target_categories = []
    target_colors = []
    
    for tr_cat, en_cats in CATEGORY_MAP.items():
        if tr_cat in query_lower:
            target_categories.extend([tr_cat] + en_cats)
            
    for tr_color, en_colors in COLOR_FAMILIES.items():
        if tr_color in query_lower:
            target_colors.extend([tr_color] + en_colors)

    results_df = items_df.copy()
    
    # Kategori Filtresi (Hem Kategori Hem İsim Sütununda Ara)
    if target_categories:
        results_df = results_df[
            results_df['category'].apply(lambda x: any(cat in str(x).lower() for cat in target_categories)) |
            results_df['name'].apply(lambda x: any(cat in str(x).lower() for cat in target_categories))
        ]
        
    # Renk Filtresi
    if target_colors:
        results_df = results_df[
            results_df['color'].apply(lambda x: any(c in str(x).lower() for c in target_colors)) |
            results_df['name'].apply(lambda x: any(c in str(x).lower() for c in target_colors))
        ]
    
    # Düz Metin Araması (Eğer yukarıdakiler boşsa)
    if results_df.empty and not target_categories and not target_colors:
         results_df = items_df[
            items_df['name'].str.contains(query_lower, na=False) |
            items_df['category'].str.contains(query_lower, na=False)
        ]

    final_items = []
    for _, row in results_df.head(40).iterrows():
        item = row.to_dict()
        if 'image' in item: item['image'] = f"/images/{os.path.basename(str(item['image']))}"
        final_items.append(item)
    return final_items

# --- ROUTES ---
@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    return jsonify({'items': strict_business_search(data.get('query', '')), 'total': 0})

@app.route('/api/combinations', methods=['POST'])
def combinations():
    try:
        data = request.json
        item_id = str(data.get('item_id'))

        found_item = items_df[items_df['item_id'] == item_id]
        selected_group = "other"
        if not found_item.empty:
            cat_str = str(found_item.iloc[0]['category']).lower()
            selected_group = determine_detailed_category(cat_str)
        
        # Yapay Zeka Modelinden Öneri Al
        ai_recommendations_ids = []
        try:
            from combin_model import get_combin_recommendations
            try: model_input_id = int(item_id)
            except: model_input_id = item_id
            
            raw_results = get_combin_recommendations(model_input_id, top_k=60)
            if not raw_results.empty:
                raw_results['item_id'] = raw_results['item_id'].astype(str)
                ai_recommendations_ids = raw_results['item_id'].tolist()
        except: pass

        # Senaryoları Belirle
        target_pool_1 = [] 
        target_pool_2 = [] 
        
        if selected_group == 'bottom': 
            # Etek/Pantolon seçilirse -> Üst + Ayakkabı
            target_pool_1 = POOL_TOPS
            target_pool_2 = POOL_SHOES
        elif selected_group == 'top': 
            # Üst seçilirse -> Alt + Ayakkabı
            target_pool_1 = POOL_BOTTOMS
            target_pool_2 = POOL_SHOES
        elif selected_group == 'outerwear':
            # Mont seçilirse -> Alt + Ayakkabı
            target_pool_1 = POOL_BOTTOMS
            target_pool_2 = POOL_SHOES
        else:
            # Ayakkabı seçilirse -> Üst + Alt
            target_pool_1 = POOL_TOPS
            target_pool_2 = POOL_BOTTOMS

        # 8 Ürüne Tamamlama Fonksiyonu (Garantili)
        def get_strictly_8_items(source_pool, count=8):
            selected = []
            pool_map = {item['item_id']: item for item in source_pool}
            
            # 1. Önce AI önerilerinden varsa ekle
            for ai_id in ai_recommendations_ids:
                if len(selected) >= count: break
                if ai_id in pool_map and ai_id != item_id:
                    selected.append(pool_map[ai_id])
            
            # 2. Eksik varsa havuzdan rastgele tamamla
            missing = count - len(selected)
            if missing > 0 and source_pool:
                excluded_ids = set([x['item_id'] for x in selected] + [item_id])
                candidates = [x for x in source_pool if x['item_id'] not in excluded_ids]
                
                if candidates:
                    take_n = min(missing, len(candidates))
                    random_picks = random.sample(candidates, take_n)
                    selected.extend(random_picks)
            
            # 3. Havuz çok küçükse ve yine de yetmediyse (Acil Durum)
            while len(selected) < count and len(source_pool) > 0:
                item = random.choice(source_pool)
                selected.append(item)

            return selected[:count]

        list_1 = get_strictly_8_items(target_pool_1, count=8)
        list_2 = get_strictly_8_items(target_pool_2, count=8)
        
        return jsonify({'recommendations': list_1 + list_2})

    except Exception as e:
        print(f"❌ Kombin Hatası: {e}")
        return jsonify({'recommendations': []})

@app.route('/api/generate-outfit', methods=['POST'])
def generate_outfit():
    if not try_on_engine: return jsonify({"status": "error", "message": "Gemini aktif değil."}), 500
    try:
        data = request.json
        web_paths = data.get('products', [])
        real_paths = [os.path.join(DATASET_IMAGES_DIR, os.path.basename(p)) for p in web_paths]
        real_paths = [p for p in real_paths if os.path.exists(p)]
        
        if not real_paths: return jsonify({"status": "error", "message": "Resim bulunamadı."}), 404

        filename = f"kombin_{int(time.time())}.png"
        path = os.path.join(GENERATED_DIR, filename)
        
        print(f"🤖 [Gemini] Görüntü işleniyor... (Lütfen bekleyiniz)")

        max_retries = 3
        for attempt in range(max_retries):
            try:
                success = try_on_engine.generate_try_on_image(
                    model_image_path=BASE_MODEL_PATH, 
                    clothing_image_paths=real_paths, 
                    output_path=path, 
                    aspect_ratio="3:4", 
                    prompt_text="A high-quality full body studio photo of a fashion model wearing this outfit. Professional lighting, white background."
                )
                if success:
                    return jsonify({"status": "success", "image_url": f"/static/generated/{filename}"})
                else:
                    time.sleep(2)
            except Exception as e:
                if "503" in str(e) or "overloaded" in str(e).lower():
                    time.sleep(4)
                else:
                    return jsonify({"status": "error", "message": str(e)}), 500

        return jsonify({"status": "error", "message": "Sunucular çok yoğun."}), 503

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/images/<path:filename>')
def serve_images(filename): return send_from_directory(DATASET_IMAGES_DIR, filename)
@app.route('/static/generated/<path:filename>')
def serve_generated(filename): return send_from_directory(GENERATED_DIR, filename)
@app.route('/static/models/<path:filename>')
def serve_models(filename): return send_from_directory(os.path.join(BASE_DIR, 'static', 'models'), filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
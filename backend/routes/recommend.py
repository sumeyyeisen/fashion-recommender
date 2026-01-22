from flask import Blueprint, request, jsonify
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../models'))

from style_model import search_by_text
from combin_model import get_combin_recommendations

recommend_bp = Blueprint('recommend', __name__)

COLOR_HARMONY = {
    'sarı': ['sarı', 'turuncu'],
    'kırmızı': ['kırmızı', 'pembe', 'bordo'],
    'mavi': ['mavi', 'lacivert'],
    'yeşil': ['yeşil'],
    'siyah': ['siyah'],
    'beyaz': ['beyaz'],
    'pembe': ['pembe'],
    'mor': ['mor'],
    'kahverengi': ['kahverengi'],
    'turuncu': ['turuncu'],
    'gri': ['gri']
}

CATEGORY_KEYWORDS = {
    'kot': 'bottoms', 'jean': 'bottoms', 'denim': 'bottoms',
    'pantolon': 'bottoms', 'pants': 'bottoms', 'trousers': 'bottoms',
    'şort': 'bottoms', 'shorts': 'bottoms', 
    'etek': 'bottoms', 'skirt': 'bottoms',
    'gömlek': 'tops', 'shirt': 'tops', 
    'tişört': 'tops', 't-shirt': 'tops', 'tshirt': 'tops',
    'kazak': 'tops', 'sweater': 'tops', 
    'bluz': 'tops', 'blouse': 'tops',
    'sweatshirt': 'tops', 'hoodie': 'tops',
    'mont': 'outerwear', 'ceket': 'outerwear', 
    'coat': 'outerwear', 'jacket': 'outerwear',
    'ayakkabı': 'shoes', 'shoes': 'shoes', 
    'bot': 'shoes', 'boots': 'shoes',
    'sandalet': 'shoes', 'sandals': 'shoes',
    'topuklu': 'shoes', 'heels': 'shoes',
    'elbise': 'all-body', 'dress': 'all-body'
}

@recommend_bp.route('/api/search', methods=['POST'])
def search():
    try:
        data = request.json
        query = data.get('query', '')
        season = data.get('season')
        has_color_keyword = data.get('has_color_keyword', False)
        top_k = data.get('limit', 8)
        
        if not query:
            return jsonify({'error': 'Query gerekli'}), 400
        
        query_lower = query.lower()
        detected_color = None
        detected_category = None
        
        for color_key in COLOR_HARMONY.keys():
            if color_key in query_lower:
                detected_color = color_key
                break
        
        for keyword, category in sorted(CATEGORY_KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True):
            if keyword in query_lower:
                detected_category = category
                break
        
        enriched_query = query
        if 'kot' in query_lower or 'jean' in query_lower or 'denim' in query_lower:
            enriched_query += ' jeans denim'
        
        results = search_by_text(
            query=enriched_query,
            top_k=top_k * 10,
            season=season,
            category=detected_category
        )
        
        items = []
        for _, row in results.iterrows():
            if detected_category and row['category'] != detected_category:
                continue
            if has_color_keyword and detected_color:
                if row['color'] == 'karışık': continue
                if detected_color in COLOR_HARMONY:
                    harmonious = COLOR_HARMONY[detected_color]
                    if row['color'] not in harmonious: continue
            
            items.append({
                'item_id': int(row['item_id']),
                'name': str(row['name']),
                'category': str(row['category']),
                'color': str(row['color']),
                'season': str(row['season']),
                'score': float(row['similarity_score']),
                'image': f"/images/{int(row['item_id'])}.jpg"
            })
            if len(items) >= top_k: break
        
        return jsonify({'success': True, 'count': len(items), 'items': items})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@recommend_bp.route('/api/combinations/<int:item_id>', methods=['GET'])
def get_combinations(item_id):
    try:
        source_season = request.args.get('source_season')
        source_category = request.args.get('source_category')
        top_k = int(request.args.get('limit', 8))
        
        results = get_combin_recommendations(
            item_id=item_id,
            top_k=top_k,
            enforce_season=source_season,
            source_category=source_category
        )
        
        items = []
        for _, row in results.iterrows():
            items.append({
                'item_id': int(row['item_id']),
                'name': str(row['name']),
                'category': str(row['category']),
                'color': str(row['color']),
                'season': str(row['season']),
                'score': float(row['score']),
                'reason': str(row['reason']),
                'image': f"/images/{int(row['item_id'])}.jpg"
            })
        
        return jsonify({
            'success': True,
            'count': len(items),
            'source_item_id': item_id,
            'recommendations': items
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@recommend_bp.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        from style_model import items_df
        return jsonify({
            'total_items': len(items_df),
            'categories': items_df['category'].value_counts().to_dict(),
            'colors': items_df['color'].value_counts().to_dict(),
            'seasons': items_df['season'].value_counts().to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
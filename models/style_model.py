import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

items_df = None
tfidf_matrix = None
vectorizer = None

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(MODEL_DIR, 'data')

def load_style_model():
    global items_df, tfidf_matrix, vectorizer
    
    if items_df is not None:
        print("✅ Stil modeli zaten yüklü.")
        return

    try:
        print("🔄 Stil modeli yükleniyor...")
        items_df = pd.read_csv(os.path.join(DATA_DIR, 'items_processed.csv'))
        with open(os.path.join(DATA_DIR, 'vectorizer.pkl'), 'rb') as f:
            vectorizer = pickle.load(f)
        
        # TF-IDF matrisi yükle
        import scipy.sparse
        tfidf_matrix = scipy.sparse.load_npz(os.path.join(DATA_DIR, 'tfidf_matrix.npz'))
        
        print(f"✅ Stil modeli yüklendi: {tfidf_matrix.shape}")
    except Exception as e:
        print(f"❌ Stil modeli hatası: {e}")

def search_by_text(query, top_k=20, category=None, color=None, season=None, exclude_mixed_colors=False):
    """
    Text araması
    
    Args:
        exclude_mixed_colors: True ise "karışık" renk kategorisini sonuçlardan çıkar
    """
    global items_df, tfidf_matrix, vectorizer
    
    if items_df is None or tfidf_matrix is None:
        return pd.DataFrame()
    
    try:
        query_vec = vectorizer.transform([query.lower()])
        similarities = cosine_similarity(query_vec, tfidf_matrix)[0]
        
        mask = np.ones(len(items_df), dtype=bool)
        
        if category:
            mask &= (items_df['category'] == category).values
        
        if color:
            mask &= (items_df['color'] == color).values
        
        if season:
            mask &= (items_df['season'] == season).values
        
        # 🚨 YENİ: Karışık rengi filtrele
        if exclude_mixed_colors:
            mask &= (items_df['color'] != 'karışık').values
        
        filtered_similarities = similarities * mask
        top_indices = np.argsort(filtered_similarities)[-top_k:][::-1]
        
        results = items_df.iloc[top_indices].copy()
        results['similarity_score'] = filtered_similarities[top_indices]
        
        return results[results['similarity_score'] > 0]
        
    except Exception as e:
        print(f"❌ Arama hatası: {e}")
        return pd.DataFrame()

def search_by_filters(category=None, color=None, season=None, limit=50):
    global items_df
    if items_df is None:
        return pd.DataFrame()
    
    mask = np.ones(len(items_df), dtype=bool)
    if category:
        mask &= (items_df['category'] == category)
    if color:
        mask &= (items_df['color'] == color)
    if season:
        mask &= (items_df['season'] == season)
    
    return items_df[mask].head(limit)

if __name__ == "__main__":
    from sklearn.feature_extraction.text import TfidfVectorizer
    from scipy.sparse import save_npz
    
    print("🔄 Stil modeli eğitiliyor...")
    items_df = pd.read_csv(os.path.join(DATA_DIR, 'polyvore_items_with_color_season.csv'))
    
    items_df['text'] = (
        items_df['name'].fillna('') + ' ' + 
        items_df['category'].fillna('') + ' ' +
        items_df['color'].fillna('') + ' ' +
        items_df['season'].fillna('')
    ).str.lower()
    
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(items_df['text'])
    
    save_npz(os.path.join(DATA_DIR, 'tfidf_matrix.npz'), tfidf_matrix)
    with open(os.path.join(DATA_DIR, 'vectorizer.pkl'), 'wb') as f:
        pickle.dump(vectorizer, f)
    
    items_df.to_csv(os.path.join(DATA_DIR, 'items_processed.csv'), index=False)
    print(f"✅ Model hazır: {tfidf_matrix.shape}")

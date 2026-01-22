# models/data_processor.py

import json
import pandas as pd
import os

# Proje ana dizininden veri setine giden yol
BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)))
DATA_PATH = os.path.join(BASE_PATH, 'dataset', 'raw')
PROCESSED_PATH = os.path.join(BASE_PATH, 'dataset', 'processed')

def load_polyvore_data(outfit_filename='train.json', item_filename='polyvore_item_metadata.json'):
    """
    Polyvore veri setini yükler ve işler.
    Outfit ID'leri ve Item ID'lerini içeren bir DataFrame döndürür.
    
    ÖNEMLİ: Bu kod, indirdiğiniz train.json dosyasının tek bir JSON listesi 
    içerdiğini varsayar. Eğer hata alırsak (bkz. json.JSONDecodeError), 
    okuma şeklini değiştireceğiz.
    """
    
    outfit_file = os.path.join(DATA_PATH, outfit_filename)
    item_file = os.path.join(DATA_PATH, item_filename)
    
    # 1. Outfit (Kombin) Verilerini Yükleme
    try:
        with open(outfit_file, 'r') as f:
            outfits_data = json.load(f)
    except FileNotFoundError:
        print(f"Hata: Outfit dosyası bulunamadı. Lütfen '{outfit_filename}' dosyasını 'dataset/raw' klasörüne koyun.")
        return None
    except json.JSONDecodeError:
        print(f"Hata: Outfit dosyası JSON formatında değil veya bozuk.")
        print("Lütfen dosyanın içeriğini kontrol edin veya satır satır JSON okuma (jsonlines) gerekip gerekmediğine bakın.")
        return None
        
    # 2. Ürün ID - İsim/Kategori Eşleşmesini Yükleme (Item Mapping)
    try:
        with open(item_file, 'r') as f:
            item_mapping = json.load(f)
    except FileNotFoundError:
        print(f"Hata: Item mapping dosyası bulunamadı. Lütfen '{item_filename}' dosyasını 'dataset/raw' klasörüne koyun.")
        item_mapping = {}
        
    print(f"Yüklenen Toplam Kombin Sayısı: {len(outfits_data)}")
    
    # 3. Kombinleri İşleme: Kombin ID'si ve İçindeki Ürün ID'lerini ayırma
    processed_list = []
    
    for outfit in outfits_data:
        outfit_id = outfit.get('set_id') # Güvenli okuma
        if not outfit_id:
            continue

        for item_info in outfit.get('items', []):
            item_id = item_info.get('item_id')
            if not item_id:
                continue
            
            # Metadata dosyasından ürün kategorisini çekme
            item_data = item_mapping.get(item_id, {})
            item_name = item_data.get('category_name', item_data.get('title', 'Bilinmeyen Ürün'))
            
            processed_list.append({
                'outfit_id': outfit_id,
                'item_id': item_id,
                'item_name': item_name 
            })
            
    df_combinations = pd.DataFrame(processed_list)
    
    # İşlenmiş veriyi kaydetme
    os.makedirs(PROCESSED_PATH, exist_ok=True)
    processed_file = os.path.join(PROCESSED_PATH, 'processed_polyvore_combinations.csv')
    df_combinations.to_csv(processed_file, index=False)
    
    print(f"İşlenmiş veri '{processed_file}' dosyasına kaydedildi.")
    print("Veri İşleme Tamamlandı.")
    print(df_combinations.head())
    
    return df_combinations

if __name__ == '__main__':
    df = load_polyvore_data()
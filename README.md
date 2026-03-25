# Fashion Recommender — Yapay Zeka Destekli Moda Asistanı

Lisans bitirme projesi. E-ticarette ürün keşfi, kombin uyumsuzluğu ve görselleştirme 
eksikliği sorunlarına yönelik üç modüllü yapay zeka tabanlı bir moda asistanı.

## Modüller

**1. Akıllı Arama**  
TF-IDF vektörizasyonu ve kosinüs benzerliği ile Türkçe metin sorgularını işler.
74.852 ürün içinde ortalama 0.34 saniyede sonuç döner. %100 başarı oranı.

**2. Kombin Önerisi**  
68.306 gerçek kombinasyondan çıkarılan 749.640 co-occurrence kuralıyla tamamlayıcı
ürün önerisi sunar. Kural bulunamayan durumlarda renk teorisi ve mevsim uyumu devreye girer.

**3. Sanal Manken**  
Google Gemini 3 Pro ile seçilen kombini 2K çözünürlükte bir manken üzerinde görselleştirir.
27/27 testte başarılı, ortalama 18.4 saniye üretim süresi.

## Teknolojiler

**Backend:** Python, Flask, Pandas, NumPy, Scikit-learn  
**Frontend:** React 18, Vite, Tailwind CSS  
**AI:** TF-IDF + Kosinüs Benzerliği, Co-occurrence Analizi, Google Gemini 3 Pro  
**Optimizasyon:** Singleton Pattern, Sparse Matrix (NPZ)  
**Veri Seti:** Polyvore Outfit Dataset — 74.852 ürün, 749.640 kombinasyon

## Kurulum
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install flask flask-cors pandas numpy scikit-learn google-generativeai pillow
python app.py

# Frontend
cd frontend
npm install
npm run dev

## Proje Hakkında

Mehmet Akif Ersoy Üniversitesi, Yazılım Mühendisliği — Bitirme Projesi  
Geliştirici: Sümeyye İsen | Danışman: Doç. Dr. İhsan Pençe | 2025-2026

# Fashion Recommender - AI-Powered Style Assistant

Yapay zeka destekli moda önerme sistemi. Metin tabanlı arama, akıllı kombin önerileri ve sanal manken giydirme (Virtual Try-On) özellikleri içerir.

## Özellikler

- **Akıllı Arama**: Türkçe metin girişi ile TF-IDF tabanlı anlamsal arama
- **Renk & Mevsim Filtreleme**: Otomatik renk ailesi ve mevsim tespiti
- **Kombin Önerileri**: Co-occurrence kuralları ve renk uyumu analizi
- **Sanal Manken (Virtual Try-On)**: 
  - Yisol/IDM-VTON modeli entegrasyonu
  - Kategori bazlı akıllı giydirme (üst/alt giyim)
  - Zincirleme giydirme (kombin oluşturma)

## Teknolojiler

**Backend:**
- Flask (Python Web Framework)
- Pandas, NumPy (Veri İşleme)
- Scikit-learn (TF-IDF Vektörizasyon)
- Gradio Client (Hugging Face API Entegrasyonu)
- OpenCV (Görüntü İşleme - Opsiyonel)

**Frontend:**
- React.js + Vite
- Vanilla CSS (Responsive Tasarım)

**AI Modelleri:**
- TF-IDF (Text Search)
- Yisol/IDM-VTON (Virtual Try-On)
- Custom Co-occurrence Rules (Kombin Önerileri)

## Kurulum

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install flask flask-cors pandas numpy scikit-learn gradio-client opencv-python
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Proje Hakkında

Bu proje, [Mehmet Akif Ersoy Üniversitesi] [Yazılım Mühendisliği] lisans bitirme projesi kapsamında geliştirilmiştir.

**Geliştirici:** [Sümeyye İsen]  
**Danışman:** [İhsan Pençe]  
**Yıl:** 2025-2026

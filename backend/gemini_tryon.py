import os
from google import genai
from google.genai import types
from PIL import Image

class GeminiTryOnGenerator:
    def __init__(self, api_key):
        """
        Gemini istemcisini başlatır.
        """
        if not api_key:
            raise ValueError("API Key bulunamadı! Lütfen geçerli bir Google API Key girin.")
        
        print("--- [GeminiTryOn] İstemci Başlatılıyor... ---")
        self.client = genai.Client(api_key=api_key)
        # Model adı
        self.model_name = "gemini-3-pro-image-preview"
        print("--- [GeminiTryOn] İstemci Hazır ✅ ---")

    def generate_try_on_image(self, 
                              model_image_path, 
                              clothing_image_paths, 
                              output_path="deneme_sonucu.png",
                              prompt_text="A high-quality studio photograph of the model wearing these clothes collectively.",
                              aspect_ratio="2:3",
                              resolution="2K"):
        """
        Manken ve kıyafet görsellerini alıp giydirilmiş fotoğrafı üretir.
        """
        print(f"--- [GeminiTryOn] Görüntü Üretiliyor... (Bu işlem 10-30sn sürebilir) ---")
        try:
            # 1. Görselleri Hazırla
            contents = []
            contents.append(prompt_text)
            
            # Manken
            if os.path.exists(model_image_path):
                contents.append(Image.open(model_image_path))
            else:
                 print(f"HATA: Manken resmi bulunamadı: {model_image_path}")
                 return False

            # Kıyafetler
            for cloth_path in clothing_image_paths:
                if os.path.exists(cloth_path):
                    contents.append(Image.open(cloth_path))
                else:
                    print(f"UYARI: Kıyafet resmi atlandı (bulunamadı): {cloth_path}")
            
            if len(contents) < 3:
                 print("HATA: Yeterli görsel sağlanmadı.")
                 return False

            # 2. İsteği Gönder
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=['IMAGE'],
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                        image_size=resolution
                    ),
                )
            )

            # 3. Sonucu Kaydet
            for part in response.parts:
                if image := part.as_image():
                    image.save(output_path)
                    print(f"--- [GeminiTryOn] BAŞARILI! Görsel kaydedildi: {output_path} 🎉 ---")
                    return True
            
            print("--- [GeminiTryOn] HATA: API görsel döndürmedi. ---")
            return False

        except Exception as e:
            print(f"--- [GeminiTryOn] KRİTİK HATA: {e} ---")
            return False

# =========================================
# TEST ALANI
# =========================================
if __name__ == "__main__":
    # SENİN API ANAHTARIN BURAYA EKLENDİ
    from dotenv import load_dotenv; load_dotenv(); MY_API_KEY = os.getenv("GOOGLE_API_KEY")

    # Dosya isimlerinin klasöründekilerle birebir aynı olduğundan emin ol
    manken_resmi = "manken.jpg" 
    kiyafetler = ["tisort_urun.jpg", "pantolon_urun.jpg"]
    sonuc_dosyasi = "test_kombin_sonucu.png"

    print(f"Test Başlıyor... \nManken: {manken_resmi}\nKıyafetler: {kiyafetler}")

    generator = GeminiTryOnGenerator(api_key=MY_API_KEY)

    basarili = generator.generate_try_on_image(
        model_image_path=manken_resmi,
        clothing_image_paths=kiyafetler,
        output_path=sonuc_dosyasi
    )

    if basarili:
        print("✅ Test başarıyla tamamlandı.")
    else:
        print("❌ Test başarısız oldu. Lütfen yukarıdaki hata mesajını oku.")

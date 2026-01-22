import { useState, useEffect, useRef } from 'react';
import api, { API_BASE_URL } from './api'; // 1. Değişiklik: API_BASE_URL import edildi
import './App.css';

function App() {
  const [products, setProducts] = useState([]); 
  const [recommendations, setRecommendations] = useState([]); 
  
  // SEÇİLEN ÜRÜNLERİN DOSYA YOLLARINI TUTAN LİSTE (SEPET)
  const [selectedItems, setSelectedItems] = useState([]); 
  
  const [searchQuery, setSearchQuery] = useState("");
  
  // 2. Değişiklik: Sabit URL yerine değişkenden çekiyoruz
  const [mannequinUrl, setMannequinUrl] = useState(`${API_BASE_URL}/static/models/base_model.jpg`);
    
  const [isLoading, setIsLoading] = useState(false);
  const [loadingText, setLoadingText] = useState("HAZIRLANIYOR");
  const [stats, setStats] = useState({ total_items: 0 });

  const recSectionRef = useRef(null);

  useEffect(() => {
    fetchProducts();
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const data = await api.getStats();
      setStats(data);
    } catch(e) { console.error(e); }
  }

  const fetchProducts = async (query = "") => {
    try {
      const data = await api.searchByText(query);
      setProducts(data.items || []);
      setRecommendations([]); 
    } catch (error) { console.error("Hata:", error); }
  };

  const fetchRecommendations = async (item) => {
    try {
        const data = await api.getCombinations(item.item_id);
        setRecommendations(data.recommendations || []);
        
        setTimeout(() => {
            if(recSectionRef.current) {
                recSectionRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        }, 100);

    } catch(e) {
        console.error("Kombin hatası:", e);
    }
  };

  const handleSearch = (e) => {
    setSearchQuery(e.target.value);
    setTimeout(() => { fetchProducts(e.target.value); }, 600);
  };

  const toggleSelection = (item, fromRecommendation = false) => {
    let imagePath = item.image;
    if (imagePath.startsWith('/')) {
        imagePath = imagePath.substring(1); 
    }

    if (selectedItems.includes(imagePath)) {
        setSelectedItems(selectedItems.filter(path => path !== imagePath));
    } else {
        setSelectedItems([...selectedItems, imagePath]);
        if (!fromRecommendation) {
            fetchRecommendations(item);
        }
    }
  };

  // --- GEMINI İLE GİYDİRME ---
  const handleGenerateOutfit = async () => {
    if (selectedItems.length === 0) {
        alert("Lütfen önce listeden giydirmek istediğin kıyafetleri seç!");
        return;
    }

    setIsLoading(true);
    setLoadingText("YAPAY ZEKA GİYDİRİYOR...");
    
    const steps = ["BEDEN ANALİZİ...", "KIYAFETLER EŞLEŞTİRİLİYOR...", "MANKEN GİYDİRİLİYOR...", "SON RÖTUŞLAR..."];
    let stepIndex = 0;
    const interval = setInterval(() => {
        setLoadingText(steps[stepIndex % steps.length]);
        stepIndex++;
    }, 4000);

    try {
      const data = await api.generateOutfit(selectedItems);

      if (data.status === 'success') {
        // 3. Değişiklik: Gelen resmi gösterirken base URL kullanıyoruz
        setMannequinUrl(`${API_BASE_URL}${data.image_url}?t=${new Date().getTime()}`);
      } else {
        alert("Hata: " + (data.message || "İşlem başarısız"));
      }
    } catch (error) {
      console.error(error);
      alert("Bağlantı hatası veya süre aşımı.");
    } finally {
      clearInterval(interval);
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedItems([]);
    // 4. Değişiklik: Resetlerken base URL kullanıyoruz
    setMannequinUrl(`${API_BASE_URL}/static/models/base_model.jpg`);
    setRecommendations([]);
  };

  return (
    <div className="app-container">
      <div className="shop-section">
        <header className="shop-header">
          <h1 className="brand-title">VIRTUAL<span>CLOSET</span></h1>
          <div className="search-container">
            <input 
                type="text" className="search-input" 
                placeholder="DOLAPTA ARA" 
                value={searchQuery} onChange={handleSearch}
            />
          </div>
        </header>

        {/* ANA ÜRÜN LİSTESİ */}
        <div className="products-grid">
          {products.map((item) => {
            let rawPath = item.image.startsWith('/') ? item.image.substring(1) : item.image;
            const isSelected = selectedItems.includes(rawPath);

            return (
                <div key={item.item_id} className={`product-card ${isSelected ? 'selected-card' : ''}`}>
                <div className="product-image-wrapper">
                    {/* 5. Değişiklik: Resim src kısmında base URL */}
                    <img 
                    src={`${API_BASE_URL}${item.image}`} 
                    alt={item.name} className="product-image"
                    onError={(e) => {e.target.src = "https://via.placeholder.com/300?text=IMG"}}
                    />
                    {isSelected && <div className="selected-badge">✓ SEÇİLDİ</div>}
                </div>
                <div className="product-details">
                    <div className="product-name" title={item.name}>{item.name}</div>
                    <button 
                    className={`action-btn ${isSelected ? 'btn-remove' : 'btn-add'}`}
                    onClick={() => toggleSelection(item, false)}
                    disabled={isLoading}
                    >
                    {isSelected ? "ÇIKAR" : "SEÇ"}
                    </button>
                </div>
                </div>
            );
          })}
        </div>

        {/* KOMBİN / ÖNERİ ALANI */}
        <div ref={recSectionRef} className="rec-section-wrapper">
            {recommendations.length > 0 && (
                <div className="recommendations-container">
                    <h2 className="rec-heading">TAMAMLAYICI PARÇALAR</h2>
                    <div className="products-grid">
                        {recommendations.map((rec) => {
                            let rawPath = rec.image.startsWith('/') ? rec.image.substring(1) : rec.image;
                            const isSelected = selectedItems.includes(rawPath);
                            
                            return (
                                <div key={rec.item_id} className={`product-card rec-card-style ${isSelected ? 'selected-card' : ''}`}>
                                    <div className="rec-badge">ÖNERİ</div>
                                    <div className="product-image-wrapper">
                                        {/* 6. Değişiklik: Öneri resimlerinde base URL */}
                                        <img 
                                            src={`${API_BASE_URL}${rec.image}`} 
                                            alt={rec.name} className="product-image"
                                            onError={(e) => {e.target.src = "https://via.placeholder.com/300?text=IMG"}}
                                        />
                                        {isSelected && <div className="selected-badge">✓</div>}
                                    </div>
                                    <div className="product-details">
                                        <div className="product-name">{rec.name}</div>
                                        <button 
                                            className={`action-btn ${isSelected ? 'btn-remove' : 'btn-add'}`}
                                            onClick={() => toggleSelection(rec, true)}
                                            disabled={isLoading}
                                        >
                                            {isSelected ? "ÇIKAR" : "EKLE"}
                                        </button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
        
        <div style={{ height: "150px" }}></div>
      </div>

      {/* SAĞ TARAFTAKİ DENEME KABİNİ (SIDEBAR) */}
      <div className="fitting-room-sidebar">
        <div className="sidebar-header">
          <div className="sidebar-title">SANAL KABİN</div>
          <div className="selected-count">
            {selectedItems.length} Parça Seçildi
          </div>
        </div>
        
        <div className="mannequin-wrapper">
          <img 
            src={mannequinUrl} alt="Virtual Mannequin" className="mannequin-image"
            onError={(e) => { e.target.src = "https://via.placeholder.com/400x600?text=MANKEN"; }}
          />
          {isLoading && (
            <div className="loading-overlay">
              <div className="spinner"></div>
              <div className="loading-text">{loadingText}</div>
            </div>
          )}
        </div>

        <div className="sidebar-controls">
          <button 
            className="try-on-btn" 
            onClick={handleGenerateOutfit} 
            disabled={isLoading || selectedItems.length === 0}
            style={{ 
                background: isLoading ? '#ccc' : '#7d548aff', 
                color: 'white', fontWeight: 'bold', padding: '15px' 
            }}
          >
            {isLoading ? "BEKLEYİNİZ..." : "MANKENİ GİYDİR"}
          </button>

          <button className="reset-btn" onClick={handleReset} disabled={isLoading}>
            TEMİZLE & SIFIRLA
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
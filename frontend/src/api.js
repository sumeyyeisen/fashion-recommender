
export const API_BASE_URL = 'http://localhost:5000';

export const api = {
  // 1. Arama
  async searchByText(query, filters = {}) {
    const response = await fetch(`${API_BASE_URL}/api/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        season: filters.season,
        category: filters.category,
        color: filters.color,
        has_color_keyword: filters.has_color_keyword || false,
        limit: filters.limit || 20
      })
    });
    return response.json();
  },

  // 2. Kombin
  async getCombinations(itemId, filters = {}) {
    const response = await fetch(`${API_BASE_URL}/api/combinations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        item_id: itemId,
        limit: filters.limit || 8,
        source_season: filters.source_season,
        source_category: filters.source_category
      })
    });
    return response.json();
  },

  // 3. Toplu Giydirme
  async generateOutfit(productPaths) {
    const response = await fetch(`${API_BASE_URL}/api/generate-outfit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        products: productPaths 
      })
    });
    return response.json();
  },

  // 4. İstatistik
  async getStats() {
    const response = await fetch(`${API_BASE_URL}/api/stats`);
    return response.json();
  }
};

export default api;
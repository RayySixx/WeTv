
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
import urllib.request
import urllib.error
import re

app = Flask(__name__)
CORS(app)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7'
}

def fetch_html(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        raise Exception(f"Gagal narik data: {str(e)}")

@app.route('/')
def home():
    return jsonify({"status": "Scraper Detektif Aktif!", "info": "Coba gunakan endpoint /search"})

@app.route('/search')
def search():
    keyword = request.args.get('keyword', '')
    if not keyword:
        return jsonify({"error": "Butuh parameter keyword"}), 400

    url = f"https://moviebox.ph/web/searchResult?keyword={keyword.replace(' ', '+')}"
    
    try:
        html = fetch_html(url)
        soup = BeautifulSoup(html, 'html.parser')
        
        results = []
        
        # STRATEGI BARBAR: Cari semua tag <a> yang punya link detail
        links = soup.find_all('a', href=True)
        for a in links:
            href = a['href']
            # Cek apakah link ini mengarah ke film
            if 'detail' in href.lower() or 'movie' in href.lower():
                img = a.find('img') or a.parent.find('img') # Cari gambar di dalam atau di dekat link
                title = a.text.strip()
                
                if img and title:
                    results.append({
                        "title": title,
                        "link": href,
                        "thumbnail": img.get('src') or img.get('data-src', ''),
                    })

        # JIKA MASIH KOSONG, TAMPILKAN HTML MENTAHNYA BIAR KITA TAU KENAPA
        if not results:
            # Cari barangkali ada data JSON tersembunyi (Next.js/Nuxt.js fallback)
            hidden_json = re.search(r'<script.*?>(\{.*?\})</script>', html)
            
            return jsonify({
                "success": False, 
                "message": "BeautifulSoup tidak menemukan data. Web kemungkinan besar menggunakan JavaScript/API terpisah (Client Side Rendering).",
                "diagnostics": {
                    "panjang_html": len(html),
                    "judul_web": soup.title.string if soup.title else "Tidak ada title",
                    "potongan_html_mentah": html[:1500] + "... (dipotong)", # Cek isinya di browser lu
                    "ada_json_tersembunyi": bool(hidden_json)
                }
            })

        return jsonify({"success": True, "data": results})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

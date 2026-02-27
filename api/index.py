from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
import urllib.request
import urllib.error
import re
import json

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
    return jsonify({"status": "Scraper Stabil Aktif!", "info": "Gunakan endpoint /search"})

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
        seen_titles = set()
        
        # STRATEGI 1: Bongkar brankas rahasia NUXT_DATA tanpa nembak API
        nuxt_script = soup.find('script', id='__NUXT_DATA__')
        if nuxt_script:
            try:
                data = json.loads(nuxt_script.string)
                # Nuxt nyimpen data dalam bentuk array datar. Kita cari yang bentuknya dictionary
                for item in data:
                    if isinstance(item, dict):
                        # Cari index yang nyimpen judul & gambar
                        title_idx = item.get('vodName') or item.get('title') or item.get('name')
                        pic_idx = item.get('vodPic') or item.get('pic') or item.get('cover')
                        
                        if isinstance(title_idx, int) and isinstance(pic_idx, int):
                            # Tarik string aslinya dari index
                            title = data[title_idx] if title_idx < len(data) else ""
                            pic = data[pic_idx] if pic_idx < len(data) else ""
                            
                            # Validasi kalau ini beneran film
                            if isinstance(title, str) and isinstance(pic, str) and len(title) > 1:
                                if title not in seen_titles and ('http' in pic or pic.startswith('/')):
                                    seen_titles.add(title)
                                    results.append({
                                        "title": title,
                                        "thumbnail": pic,
                                        "link": f"/search_result_{title.replace(' ', '_')}" # Link smentara
                                    })
            except Exception as e:
                pass # Kalau gagal ekstrak JSON, biarin aja lanjut ke Strategi 2

        # STRATEGI 2: Fallback pakai cara asli lu (Tag A) kalau NUXT kosong
        if not results:
            links = soup.find_all('a', href=True)
            for a in links:
                href = a['href']
                if 'detail' in href.lower() or 'movie' in href.lower():
                    img = a.find('img') or a.parent.find('img') 
                    title = a.text.strip()
                    
                    if img and title and title not in seen_titles:
                        seen_titles.add(title)
                        results.append({
                            "title": title,
                            "link": href,
                            "thumbnail": img.get('src') or img.get('data-src', ''),
                        })

        # FILTER SAMPAH: Buang menu-menu web yang ikut ke-scrape
        final_results = []
        sampah = ["MovieBox", "Movie", "Old Moviebox", "Always Find Us", "Official Link Release", "Contact Us"]
        
        for r in results:
            # Pastikan judulnya bukan menu web, dan linknya bukan link email/keluar
            if r['title'] not in sampah and "mailto:" not in r['link'] and "moviebox.co" not in r['link']:
                final_results.append(r)

        # Kalau beneran kosong, tampilkan pesan error
        if not final_results:
            return jsonify({
                "success": False, 
                "message": "Data film tidak ditemukan di NUXT maupun HTML.",
            })

        return jsonify({"success": True, "data": final_results})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

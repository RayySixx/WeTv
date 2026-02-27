
import urllib.request
from bs4 import BeautifulSoup
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7'
}

# --- FUNGSI BANTUAN ---
def fetch_html(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        raise Exception(f"Gagal narik HTML: {str(e)}")

def extract_nuxt_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    # Cari tag script yang isinya data JSON rahasia Nuxt
    nuxt_script = soup.find('script', id='__NUXT_DATA__')
    if not nuxt_script:
        return None
    try:
        return json.loads(nuxt_script.string)
    except:
        return None

def parse_nuxt_array(nuxt_array):
    movies = []
    seen_titles = set()
    
    # Nuxt 3 memecah data JSON jadi array index (Devalue format).
    # Kita looping buat ngerakit ulang object-object di dalamnya.
    for item in nuxt_array:
        if isinstance(item, dict):
            resolved = {}
            for key, val in item.items():
                # Jika value adalah angka, itu adalah pointer ke index array
                if isinstance(val, int) and val < len(nuxt_array):
                    resolved[key] = nuxt_array[val]
                else:
                    resolved[key] = val
            
            # Ciri-ciri data film: Punya judul dan gambar
            title = resolved.get('title') or resolved.get('name') or resolved.get('vodName') or resolved.get('movieName')
            pic = resolved.get('cover') or resolved.get('pic') or resolved.get('vodPic') or resolved.get('posterUrl') or resolved.get('coverUrl')
            
            # Validasi apakah ini beneran film
            if title and isinstance(title, str) and pic and isinstance(pic, str) and len(title) > 1:
                if title not in seen_titles and ('http' in pic or pic.startswith('/')):
                    seen_titles.add(title)
                    
                    movies.append({
                        "title": title,
                        "thumbnail": pic,
                        "id": resolved.get('id') or resolved.get('vodId') or resolved.get('movieId') or '',
                        "rating": resolved.get('score') or resolved.get('rating') or resolved.get('doubanScore') or 'N/A',
                        "year": resolved.get('year') or resolved.get('releaseYear') or ''
                    })
    return movies

# --- ENDPOINT API ---
@app.route('/')
def home():
    return jsonify({
        "status": "API Moviebox NUXT Bypass Aktif!", 
        "endpoints": ["/search?keyword=...", "/detail?url=..."]
    })

@app.route('/search')
def search():
    keyword = request.args.get('keyword', '')
    if not keyword:
        return jsonify({"error": "Butuh parameter keyword"}), 400

    url = f"https://moviebox.ph/web/searchResult?keyword={keyword.replace(' ', '+')}"
    
    try:
        html = fetch_html(url)
        nuxt_array = extract_nuxt_data(html)
        
        if not nuxt_array:
            return jsonify({"success": False, "error": "Gagal menemukan __NUXT_DATA__ di web aslinya"}), 500
            
        results = parse_nuxt_array(nuxt_array)
        
        return jsonify({
            "success": True, 
            "keyword": keyword, 
            "total_found": len(results), 
            "data": results
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/detail')
def detail():
    # Contoh pakai: /detail?url=https://moviebox.ph/detail/sweet-home-...
    target_url = request.args.get('url', '')
    if not target_url:
        return jsonify({"error": "Butuh parameter url"}), 400

    try:
        html = fetch_html(target_url)
        nuxt_array = extract_nuxt_data(html)
        
        if not nuxt_array:
            return jsonify({"success": False, "error": "Gagal menemukan __NUXT_DATA__ di web aslinya"}), 500
            
        # Karena halaman detail cuma 1 film, algoritma parse_nuxt_array 
        # bakal otomatis nangkep data film spesifik tersebut
        results = parse_nuxt_array(nuxt_array)
        
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Endpoint tidak ditemukan"}), 404

if __name__ == '__main__':
    app.run(debug=True)

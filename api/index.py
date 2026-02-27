import urllib.request
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7'
}

def fetch_html(url):
    # Dibatasi 8 detik biar Vercel nggak motong sepihak (Timeout Vercel = 10 detik)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        return str(e) # Return errornya sebagai string biar nggak crash

@app.route('/')
def home():
    return jsonify({"status": "API Moviebox Regex Mode Aktif!"})

@app.route('/search')
def search():
    keyword = request.args.get('keyword', '')
    if not keyword:
        return jsonify({"error": "Butuh parameter keyword"}), 400

    # Tetep nembak halaman WEB aslinya, BUKAN API
    url = f"https://moviebox.ph/web/searchResult?keyword={keyword.replace(' ', '+')}"
    
    try:
        html = fetch_html(url)
        
        # Kalau response dari urllib ngeluarin pesan error timeout/forbidden
        if "HTTP Error" in html or "timed out" in html.lower():
            return jsonify({
                "success": False, 
                "error": "Diblokir atau Timeout dari Moviebox",
                "detail_error": html
            }), 500

        # --- STRATEGI SUPER RINGAN: REGEX BARBAR ---
        # Kita potong bagian script NUXT_DATA biar fokus nyari data di situ
        nuxt_match = re.search(r'<script id="__NUXT_DATA__"[^>]*>(.*?)</script>', html)
        
        if not nuxt_match:
            return jsonify({
                "success": False, 
                "error": "HTML berhasil ditarik, tapi data film tidak ditemukan. Server Moviebox mungkin mengirim halaman Captcha."
            }), 500

        raw_data = nuxt_match.group(1)
        
        # Cari semua URL gambar poster pakai Regex
        # Poster Moviebox biasanya disimpen di h5-static.aoneroom.com
        posters = re.findall(r'https://h5-static[^\s"\'\\]+\.(?:jpg|png|jpeg|webp)', raw_data)
        
        # Hilangkan duplikat gambar
        unique_posters = list(set(posters))

        return jsonify({
            "success": True, 
            "message": "Berhasil menembus HTML Web Moviebox!",
            "total_poster_ditemukan": len(unique_posters),
            "data_mentah": {
                # Gua return sebagian list posternya aja dulu buat bukti kalau datanya tembus
                "thumbnails": unique_posters[:15] 
            }
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"Error internal kode: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)

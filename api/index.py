from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
import cloudscraper

app = Flask(__name__)
CORS(app) # Mengatasi error CORS saat API diakses lewat frontend HTML

# Bikin instance scraper yang nyamar jadi Chrome di Windows
# Ini otomatis nge-handle bypass dasar WAF/Cloudflare
scraper = cloudscraper.create_scraper(browser={
    'browser': 'chrome',
    'platform': 'windows',
    'desktop': True
})

@app.route('/')
def home():
    return jsonify({
        "status": "API Moviebox dengan Cloudscraper Aktif!", 
        "endpoints": ["/search?keyword=...", "/detail?url=...", "/play?url=...", "/filter?genre=..."]
    })

@app.route('/search')
def search():
    keyword = request.args.get('keyword', '')
    if not keyword:
        return jsonify({"error": "Masukkan parameter keyword"}), 400

    url = f"https://moviebox.ph/web/searchResult?keyword={keyword}"
    
    try:
        response = scraper.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        # NOTE: Class 'movie-item' wajib lu sesuaikan dengan hasil inspect element web asli
        items = soup.find_all('div', class_='movie-item') 
        
        for item in items:
            title_tag = item.find('h3')
            link_tag = item.find('a')
            img_tag = item.find('img')
            
            if title_tag and link_tag:
                results.append({
                    "title": title_tag.text.strip(),
                    "link": link_tag['href'] if link_tag.has_attr('href') else "",
                    "image": img_tag['src'] if img_tag and img_tag.has_attr('src') else ""
                })
                
        return jsonify({"success": True, "keyword": keyword, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/detail')
def detail():
    target_url = request.args.get('url')
    if not target_url:
         return jsonify({"error": "Parameter url dibutuhkan"}), 400

    try:
        response = scraper.get(target_url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # NOTE: Sesuaikan tag dan class di bawah ini
        detail_data = {
            "title": soup.find('h1').text.strip() if soup.find('h1') else "Tidak diketahui",
            "synopsis": soup.find('div', class_='desc').text.strip() if soup.find('div', class_='desc') else "",
            "poster": soup.find('img', class_='poster')['src'] if soup.find('img', class_='poster') else ""
        }
        
        return jsonify({"success": True, "data": detail_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/play')
def play():
    # URL target ini harus link yang mengarah ke 123movienow.cc
    target_url = request.args.get('url') 
    if not target_url:
         return jsonify({"error": "Parameter url dibutuhkan"}), 400
         
    try:
        response = scraper.get(target_url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        video_src = soup.find('video')
        iframe_src = soup.find('iframe')
        
        return jsonify({
            "success": True,
            "video_url": video_src['src'] if video_src and video_src.has_attr('src') else None,
            "iframe_url": iframe_src['src'] if iframe_src and iframe_src.has_attr('src') else None
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/filter')
def filter_movies():
    genre = request.args.get('genre', 'All')
    country = request.args.get('country', 'All')
    year = request.args.get('year', 'All')
    
    url = f"https://moviebox.ph/web/film?type=/home/movieFilter&tabId=2&classify=All&country={country}&genre={genre}&sort=ForYou&year={year}"
    
    try:
        response = scraper.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        items = soup.find_all('div', class_='filter-item') # Sesuaikan class
        
        for item in items:
             results.append({
                "title": item.text.strip(),
            })
            
        return jsonify({"success": True, "filters": {"genre": genre, "country": country, "year": year}, "data": results})
    except Exception as e:
         return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

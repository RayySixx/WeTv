from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Headers agar website tidak mengira kita bot
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

@app.route('/')
def home():
    return jsonify({"status": "Scraper Moviebox Jalan!", "message": "Gunakan endpoint /search, /detail, /play, atau /filter"})

# 1. Endpoint untuk Search (List Film)
@app.route('/search')
def search():
    keyword = request.args.get('keyword', '')
    url = f"https://moviebox.ph/web/searchResult?keyword={keyword}"
    
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    results = []
    # CATATAN: Class HTML di bawah ('movie-item', 'title', dll) 
    # perlu kamu sesuaikan dengan inspect element di website aslinya
    items = soup.find_all('div', class_='movie-item') 
    
    for item in items:
        results.append({
            "title": item.find('h3', class_='title').text.strip() if item.find('h3', class_='title') else None,
            "link": item.find('a')['href'] if item.find('a') else None,
            "image": item.find('img')['src'] if item.find('img') else None
        })
        
    return jsonify({"keyword": keyword, "data": results})

# 2. Endpoint untuk Detail Film
@app.route('/detail')
def detail():
    # Contoh parameter: ?url=https://moviebox.ph/detail/...
    target_url = request.args.get('url')
    if not target_url:
         return jsonify({"error": "URL detail dibutuhkan"}), 400

    response = requests.get(target_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Ganti class sesuai inspect element
    detail_data = {
        "title": soup.find('h1').text.strip() if soup.find('h1') else None,
        "synopsis": soup.find('div', class_='synopsis').text.strip() if soup.find('div', class_='synopsis') else None,
        "rating": soup.find('span', class_='rating').text.strip() if soup.find('span', class_='rating') else None
    }
    
    return jsonify({"data": detail_data})

# 3. Endpoint untuk Nonton (Video Play)
@app.route('/play')
def play():
    target_url = request.args.get('url') # URL 123movienow.cc
    if not target_url:
         return jsonify({"error": "URL video dibutuhkan"}), 400
         
    response = requests.get(target_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Target utama: Cari tag <video> atau <iframe> tempat filmnya diputar
    video_src = soup.find('video')
    iframe_src = soup.find('iframe')
    
    return jsonify({
        "video_url": video_src['src'] if video_src and 'src' in video_src.attrs else None,
        "iframe_url": iframe_src['src'] if iframe_src and 'src' in iframe_src.attrs else None
    })

# 4. Endpoint untuk Kategori / Filter
@app.route('/filter')
def filter_movies():
    # Ambil parameter dari request kamu, ada defaultnya
    genre = request.args.get('genre', 'All')
    country = request.args.get('country', 'All')
    year = request.args.get('year', 'All')
    
    url = f"https://moviebox.ph/web/film?type=/home/movieFilter&tabId=2&classify=All&country={country}&genre={genre}&sort=ForYou&year={year}"
    
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    results = []
    # Sesuaikan dengan class di halaman kategori
    items = soup.find_all('div', class_='filter-item') 
    
    for item in items:
         results.append({
            "title": item.text.strip(),
            # Tambahkan ekstraksi data lain di sini
        })
        
    return jsonify({"filters": {"genre": genre, "country": country, "year": year}, "data": results})

if __name__ == '__main__':
    app.run(debug=True)

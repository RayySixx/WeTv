from fastapi import FastAPI, HTTPException
import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote

app = FastAPI(title="Movie Scraper API")

BASE_URL = "https://shadowofthevampire.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# --- HELPER FUNCTION ---
def is_safe_content(text: str) -> bool:
    """Filter untuk membuang konten berbau 'semi'"""
    if not text:
        return True
    forbidden_words = ["semi", "film semi korea, jepang, philippines"]
    text_lower = text.lower()
    return not any(word in text_lower for word in forbidden_words)

# --- ROUTES ---

@app.get("/")
def home():
    return {"message": "Scraper API is running!", "status": "OK"}

@app.get("/api/home")
async def get_home():
    """Scrape Home & filter kategori"""
    async with httpx.AsyncClient() as client:
        response = await client.get(BASE_URL, headers=HEADERS, timeout=10.0)
        soup = BeautifulSoup(response.text, 'html.parser')

    data = []
    # Ganti 'div.category-block' dengan class pembungkus kategori di web aslinya
    categories = soup.find_all('div', class_='category-block') 

    for cat in categories:
        cat_title_tag = cat.find('h2') # Misal judul kategori pakai <h2>
        cat_title = cat_title_tag.text.strip() if cat_title_tag else "Unknown"

        # FILTERING KATEGORI
        if not is_safe_content(cat_title):
            continue

        movies = []
        # Ganti 'article.item' dengan class item filmnya
        items = cat.find_all('article', class_='item') 
        for item in items:
            title = item.find('h3').text.strip() if item.find('h3') else ""
            thumb = item.find('img')['src'] if item.find('img') else ""
            rating = item.find('span', class_='rating').text.strip() if item.find('span', class_='rating') else ""
            link = item.find('a')['href'] if item.find('a') else ""

            movies.append({
                "title": title,
                "thumbnail": thumb,
                "rating": rating,
                "endpoint": link.replace(BASE_URL, "")
            })

        data.append({
            "category": cat_title,
            "movies": movies
        })

    return {"result": data}


@app.get("/api/stream")
async def get_stream(endpoint: str):
    """Scrape halaman streaming beserta detail meta datanya"""
    url = f"{BASE_URL}{endpoint}" if endpoint.startswith("/") else f"{BASE_URL}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS, timeout=10.0)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Film tidak ditemukan")
        soup = BeautifulSoup(response.text, 'html.parser')

    # Parsing Deskripsi (Ganti class sesuai web)
    description = soup.find('div', class_='description').text.strip() if soup.find('div', class_='description') else ""
    
    # Parsing Meta Data
    meta_data = {}
    meta_ul = soup.find('ul', class_='meta-list') # Ganti sesuai container meta
    if meta_ul:
        for li in meta_ul.find_all('li'):
            key_tag = li.find('b')
            if key_tag:
                key = key_tag.text.replace(':', '').strip()
                val = li.text.replace(key_tag.text, '').strip()
                meta_data[key] = val

    # Filter by Genre dari Meta Data
    if "Genre" in meta_data and not is_safe_content(meta_data["Genre"]):
        raise HTTPException(status_code=403, detail="Konten tidak diizinkan (Genre diblokir)")

    # Parsing Video Iframe & Server
    iframe_tag = soup.find('iframe')
    video_url = iframe_tag['src'] if iframe_tag else ""

    servers = []
    server_list = soup.find_all('a', class_='server-btn') # Ganti sesuai tombol server
    for srv in server_list:
        servers.append({"name": srv.text.strip(), "link": srv.get('href', '')})

    return {
        "title": soup.find('h1').text.strip() if soup.find('h1') else "Unknown",
        "description": description,
        "meta": meta_data,
        "video_iframe": video_url,
        "servers": servers
    }


@app.get("/api/search")
async def search_movies(q: str):
    """Scrape fitur pencarian"""
    url = f"{BASE_URL}/?s={quote(q)}&post_type[]=post&post_type[]=tv"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS, timeout=10.0)
        soup = BeautifulSoup(response.text, 'html.parser')

    results = []
    items = soup.find_all('article', class_='item') # Sesuaikan class
    
    for item in items:
        # Coba ambil genre (biasanya di pencarian ada label genre)
        genre_tag = item.find('span', class_='genre')
        genre_text = genre_tag.text.strip() if genre_tag else ""

        # FILTERING GENRE PADA HASIL PENCARIAN
        if not is_safe_content(genre_text):
            continue

        title = item.find('h3').text.strip() if item.find('h3') else ""
        thumb = item.find('img')['src'] if item.find('img') else ""
        rating = item.find('span', class_='rating').text.strip() if item.find('span', class_='rating') else ""
        link = item.find('a')['href'] if item.find('a') else ""

        results.append({
            "title": title,
            "thumbnail": thumb,
            "rating": rating,
            "genre": genre_text,
            "endpoint": link.replace(BASE_URL, "")
        })

    return {"query": q, "total": len(results), "results": results}


@app.get("/api/filter/{filter_type}/{filter_value}")
async def filter_movies(filter_type: str, filter_value: str):
    """
    Handle route seperti:
    - /action/ -> filter_type='genre', filter_value='action'
    - /year/2016/ -> filter_type='year', filter_value='2016'
    """
    # Sesuaikan URL pattern dari web aslinya
    if filter_type == "genre":
        url = f"{BASE_URL}/{filter_value}/"
    else:
        url = f"{BASE_URL}/{filter_type}/{filter_value}/"

    # Jika user maksa buka genre semi via URL API lu, langsung tolak
    if filter_type == "genre" and not is_safe_content(filter_value):
        raise HTTPException(status_code=403, detail="Kategori diblokir")

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS, timeout=10.0)
        soup = BeautifulSoup(response.text, 'html.parser')

    results = []
    items = soup.find_all('article', class_='item') # Sesuaikan class
    
    for item in items:
        title = item.find('h3').text.strip() if item.find('h3') else ""
        thumb = item.find('img')['src'] if item.find('img') else ""
        link = item.find('a')['href'] if item.find('a') else ""

        results.append({
            "title": title,
            "thumbnail": thumb,
            "endpoint": link.replace(BASE_URL, "")
        })

    return {"filter": f"{filter_type}: {filter_value}", "results": results}

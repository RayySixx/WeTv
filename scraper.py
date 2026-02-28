import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

BASE_URL = "https://shadowofthevampire.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_soup(url):
    """Mengambil dan memparsing halaman HTML."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_movie_item(item):
    """Ekstrak data dari elemen film (biasanya <article> atau <div>)."""
    # Sesuaikan selector dengan struktur HTML situs (contoh sementara)
    link_elem = item.find('a', href=True)
    if not link_elem:
        return None
    link = urljoin(BASE_URL, link_elem['href'])
    title_elem = item.find('h2') or item.find('h3') or item.find('h4')
    title = title_elem.get_text(strip=True) if title_elem else ''
    img_elem = item.find('img')
    thumbnail = img_elem.get('src') if img_elem else ''
    if thumbnail and not thumbnail.startswith('http'):
        thumbnail = urljoin(BASE_URL, thumbnail)
    rating_elem = item.find(class_=re.compile(r'rating|nilai|imdb'))
    rating = rating_elem.get_text(strip=True) if rating_elem else ''
    return {
        'title': title,
        'thumbnail': thumbnail,
        'rating': rating,
        'link': link
    }

def scrape_home_categories():
    """
    Mengambil film dari halaman utama berdasarkan kategori:
    - REKOMENDASI FILM
    - NONTON FILM & DRAMA KOREA
    - LAST MOVIES
    (Kategori Semi diabaikan)
    """
    soup = get_soup(BASE_URL)
    if not soup:
        return []
    
    # Cari semua heading kategori (misal <h2> atau <h3>)
    categories = []
    for heading in soup.find_all(['h2', 'h3']):
        cat_name = heading.get_text(strip=True).upper()
        if cat_name in ['REKOMENDASI FILM', 'NONTON FILM & DRAMA KOREA', 'LAST MOVIES']:
            # Ambil container setelah heading (misal <div class="movies">)
            container = heading.find_next_sibling('div')
            if not container:
                # Mungkin di dalam parent yang sama
                container = heading.parent.find_next_sibling('div')
            if container:
                movies = []
                for item in container.find_all('article'):  # atau class tertentu
                    movie = extract_movie_item(item)
                    if movie:
                        movies.append(movie)
                categories.append({
                    'category': cat_name,
                    'movies': movies
                })
    return categories

def scrape_movie_detail(url):
    """Mengambil detail film dari halaman stream."""
    soup = get_soup(url)
    if not soup:
        return {}
    
    # 1. Video & server
    servers = []
    # Cari elemen iframe video utama
    iframe = soup.find('iframe')
    if iframe and iframe.get('src'):
        servers.append({
            'server': 'Default',
            'url': iframe['src']
        })
    # Cari kemungkinan beberapa server (misal tab)
    server_tabs = soup.find_all(class_=re.compile(r'server|tab'))
    for tab in server_tabs:
        server_name = tab.get_text(strip=True)
        # Cari iframe terkait
        related_iframe = tab.find_next('iframe')
        if related_iframe:
            servers.append({
                'server': server_name,
                'url': related_iframe['src']
            })
    
    # 2. Deskripsi dan metadata
    # Cari elemen deskripsi (misal <div class="desc"> atau <p>)
    desc_elem = soup.find(class_=re.compile(r'desc|sinopsis|deskripsi'))
    if not desc_elem:
        desc_elem = soup.find('p')
    description_text = desc_elem.get_text(strip=True) if desc_elem else ''
    
    # Metadata tambahan (By, Posted on, Genre, dll)
    metadata = {}
    # Cari teks setelah deskripsi, biasanya dalam format "By: ... Posted on: ..."
    # Bisa menggunakan regex
    text = soup.get_text()
    patterns = {
        'by': r'By[:\s]*([^\n]+)',
        'posted_on': r'Posted on[:\s]*([^\n]+)',
        'genre': r'Genre[:\s]*([^\n]+)',
        'year': r'Year[:\s]*([^\n]+)',
        'duration': r'Duration[:\s]*([^\n]+)',
        'country': r'Country[:\s]*([^\n]+)',
        'release': r'Release[:\s]*([^\n]+)',
        'language': r'Language[:\s]*([^\n]+)',
        'director': r'Director[:\s]*([^\n]+)',
        'cast': r'Cast[:\s]*([^\n]+)'
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            metadata[key] = match.group(1).strip()
    
    return {
        'url': url,
        'servers': servers,
        'description': description_text,
        'metadata': metadata
    }

def search(query):
    """Mencari film berdasarkan kata kunci."""
    url = f"{BASE_URL}/?s={query}&post_type[]=post&post_type[]=tv"
    soup = get_soup(url)
    if not soup:
        return []
    movies = []
    for item in soup.find_all('article'):  # sesuaikan selector
        movie = extract_movie_item(item)
        # Ambil genre dari listing jika ada
        genre_elem = item.find(class_=re.compile(r'genre'))
        if genre_elem:
            movie['genres'] = genre_elem.get_text(strip=True).split(',')
        if movie:
            movies.append(movie)
    return movies

def filter_by_genre(genre):
    """Mengambil film berdasarkan genre."""
    url = f"{BASE_URL}/{genre}/"
    soup = get_soup(url)
    if not soup:
        return []
    movies = []
    for item in soup.find_all('article'):
        movie = extract_movie_item(item)
        if movie:
            movies.append(movie)
    return movies

def filter_by_year(year):
    url = f"{BASE_URL}/year/{year}/"
    soup = get_soup(url)
    if not soup:
        return []
    movies = []
    for item in soup.find_all('article'):
        movie = extract_movie_item(item)
        if movie:
            movies.append(movie)
    return movies

def filter_by_country(country):
    url = f"{BASE_URL}/country/{country}/"
    soup = get_soup(url)
    if not soup:
        return []
    movies = []
    for item in soup.find_all('article'):
        movie = extract_movie_item(item)
        if movie:
            movies.append(movie)
    return movies

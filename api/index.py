from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "sukses",
        "pesan": "API Vercel Python jalan bro!"
    })

@app.route('/scrape')
def scrape_wetv():
    # Ini cuma contoh pakai requests biasa (kemungkinan cuma dapet kerangka HTML WeTV)
    url = "https://wetv.vip/id"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ngambil title web buat ngetes doang
        title = soup.title.string if soup.title else "Gak dapet title"
        
        return jsonify({
            "status": "sukses",
            "title_web": title,
            "catatan": "Kalau datanya kosong, berarti WeTV nge-render pakai JS."
        })
    except Exception as e:
        return jsonify({"status": "error", "pesan": str(e)})

# Vercel butuh variable 'app' buat ngejalanin Flask-nya

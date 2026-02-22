from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import os

app = Flask(__name__)

def scrape_wetv(url):
    with sync_playwright() as p:
        # Kita pakai chromium, tapi tanpa download full browser di runtime
        # Vercel butuh executable path yang benar jika pakai custom layer, 
        # tapi untuk basic, kita coba headless standar dulu.
        try:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Berpura-pura jadi user beneran agar tidak di-block
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
            })

            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Tunggu selector judul filmnya muncul
            page.wait_for_selector(".video_title", timeout=5000)

            result = {
                "title": page.inner_text(".video_title").strip(),
                "episode": page.inner_text(".episode_item.active").strip() if page.query_selector(".episode_item.active") else "Single/Movie",
                "status": "success"
            }
            browser.close()
            return result
        except Exception as e:
            if 'browser' in locals(): browser.close()
            return {"status": "error", "message": str(e)}

@app.route('/api/scrape')
def api_scrape():
    target_url = request.args.get('url')
    if not target_url:
        return jsonify({"error": "Mana link-nya bro?"}), 400
    return jsonify(scrape_wetv(target_url))

@app.route('/')
def home():
    return "WeTV Scraper is Active!"

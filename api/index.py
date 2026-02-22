from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import os

app = Flask(__name__)

def scrape_wetv(url):
    with sync_playwright() as p:
        # Launch browser (chromium)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # Buka URL dengan timeout 30 detik
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Tunggu element judul muncul
            page.wait_for_selector(".video_title", timeout=10000)
            
            # Ambil data
            data = {
                "title": page.inner_text(".video_title"),
                "description": page.inner_text(".video_desc") if page.query_selector(".video_desc") else "No description",
                "current_episode": page.inner_text(".episode_item.active") if page.query_selector(".episode_item.active") else "Unknown",
                "status": "success"
            }
        except Exception as e:
            data = {"status": "error", "message": str(e)}
        
        browser.close()
        return data

@app.route('/api/scrape', methods=['GET'])
def api_scrape():
    target_url = request.args.get('url')
    if not target_url:
        return jsonify({"error": "Kasih parameter ?url= link wetv nya bro"}), 400
    
    result = scrape_wetv(target_url)
    return jsonify(result)

# Root route
@app.route('/')
def home():
    return "WeTV Scraper API is Running!"

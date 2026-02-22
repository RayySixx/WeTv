import requests
import re
from flask import Flask, request, jsonify

app = Flask(__name__)

def extract_ids(url):
    # Regex buat ambil CID dan VID dari URL WeTV
    # Contoh: /play/19q8yj9d3bzqfqk/y0047fbi20b
    match = re.search(r'play/([^/]+)/?([^/]+)?', url)
    if match:
        return match.group(1), match.group(2)
    return None, None

def get_wetv_metadata(cid, vid=None):
    # API Endpoint Internal WeTV
    url = "https://v.wetv.vip/gw/multi-vinfo"
    
    params = {
        "is_all": 1,
        "cid": cid,
        "vid": vid if vid else "",
        "lang": "id",
        "platform": 48, # Platform code buat Web/Mobile API
        "version": "1.0"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://wetv.vip/",
        "Origin": "https://wetv.vip"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        res_json = response.json()
        
        # Ambil data utama dari response WeTV
        data = res_json.get("data", {})
        video_info = data.get("videoInfo", {})
        
        return {
            "status": "success",
            "title": video_info.get("title"),
            "description": video_info.get("desc"),
            "cover": video_info.get("vertical_pic_url"),
            "year": video_info.get("publish_date"),
            "episode_title": data.get("episodeInfo", {}).get("title"),
            "total_episodes": video_info.get("episode_all_cnt"),
            "is_vip": video_info.get("is_vip") == "1"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/api/scrape')
def api_scrape():
    target_url = request.args.get('url')
    if not target_url:
        return jsonify({"error": "Masukin parameter ?url= link wetv nya"}), 400
    
    cid, vid = extract_ids(target_url)
    if not cid:
        return jsonify({"error": "URL gak valid, pastikan ada /play/ID_NYA"}), 400
        
    result = get_wetv_metadata(cid, vid)
    return jsonify(result)

@app.route('/')
def home():
    return "WeTV API Scraper - Direct Mode Active"

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/api/build', methods=['POST'])
def build_app():
    try:
        # 1. Ambil data dari form HTML
        website_url = request.form.get('url')
        app_name = request.form.get('appName')
        email = request.form.get('email')
        icon_file = request.files.get('icon')

        if not all([website_url, app_name, email, icon_file]):
            return jsonify({"status": "error", "message": "Semua data wajib diisi!"}), 400

        # 2. Setup Session untuk request ke Median.co
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://median.co/"
        }

        # --- PERHATIAN: GANTI ENDPOINT DI BAWAH SESUAI HASIL INSPECT NETWORK ---
        
        # A. Create App
        create_payload = {"websiteUrl": website_url, "appName": app_name, "email": email}
        # req_create = session.post("URL_ASLI_CREATE_DARI_NETWORK_TAB", json=create_payload, headers=headers)
        # app_id = req_create.json().get("appId") 
        
        # B. Upload Icon
        # icon_data = icon_file.read() # Baca file ke memori (karena Vercel serverless)
        # files = {'file': (icon_file.filename, icon_data, icon_file.mimetype)}
        # req_upload = session.post(f"URL_ASLI_UPLOAD/{app_id}/icon", files=files, headers=headers)
        
        # C. Trigger Build
        # req_build = session.post(f"URL_ASLI_BUILD/{app_id}/build", headers=headers)

        # --- BATAS KODE YANG HARUS DISESUAIKAN ---

        # SIMULASI RESPONSE (Hapus ini jika kode di atas sudah berjalan):
        app_id = "7qaqzjbvzrjaqmjvyadxjvzhac" # Contoh ID dummy

        # 3. Kembalikan link status ke Frontend
        check_url = f"https://median.co/app/{app_id}/build#app-download"
        
        return jsonify({
            "status": "success",
            "message": "Aplikasi sedang diproses di server Median!",
            "data": {
                "app_id": app_id,
                "check_url": check_url
            }
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Wajib untuk Vercel Serverless
if __name__ == '__main__':
    app.run(debug=True)

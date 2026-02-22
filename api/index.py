from flask import Flask, jsonify

app = Flask(__name__)

# Ini trik biar URL apapun yang diketik (misal /scrape, /test) tetep masuk ke sini
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return jsonify({
        "status": "sukses",
        "pesan": "Alhamdulillah Python di Vercel jalan bro!",
        "path_yang_diakses": path
    })

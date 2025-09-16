#!/usr/bin/env python3
"""
safetest_landing.py
Small Flask app to serve a safe landing page for the lab exercise and log clicks.
- Logs: token, timestamp, client_ip, user_agent to clicks.csv
- Shows clear educational message and link to training material
Run with: python3 safetest_landing.py
"""

from flask import Flask, request, render_template_string
from datetime import datetime
import csv
from pathlib import Path

APP_PORT = 5000
LOG_FILE = "clicks.csv"

app = Flask(__name__)

LANDING_HTML = """
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Offre exclusive</title></head>
<body>
  <div style="border:3px solid #cc0000;padding:12px;">
    <h1 style="color:#cc0000;">Offre exclusive</h1>
    <p>Pour beneficier de l'offre veuillez saisir vos informations de connexion et acceder au site.</p>
    <input type="text" placeholder="Nom d'utilisateur"/><br/>
    <input type="text" placeholder="Numero du client"/><br/>
    <button>Valider</button>
    <p>Token de test : <code>{{ token }}</code></p>
  </div>
</body>
</html>
"""

def append_click(row):
    header = ["timestamp","token","client_ip","user_agent"]
    exists = Path(LOG_FILE).exists()
    with open(LOG_FILE, "a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(header)
        writer.writerow(row)

@app.route("/landing")
def landing():
    token = request.args.get("token","-")
    ts = datetime.utcnow().isoformat()+"Z"
    client_ip = request.remote_addr
    ua = request.headers.get("User-Agent","-")
    append_click([ts, token, client_ip, ua])
    return render_template_string(LANDING_HTML, token=token)

if __name__ == "__main__":
    print(f"Starting Flask landing app on port {APP_PORT} (listen on 0.0.0.0 recommended for lab network)")
    app.run(host="0.0.0.0", port=APP_PORT)

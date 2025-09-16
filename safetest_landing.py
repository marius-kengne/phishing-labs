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
import json
from datetime import datetime
from pathlib import Path
from flask import request, render_template_string, jsonify
APP_PORT = 5000
LOG_FILE = "clicks.csv"
SUBMISSIONS_FILE = "submissions.csv"
app = Flask(__name__)

LANDING_HTML = """
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Offre exclusive</title></head>
<body>

  <form method="post" action="/submit" style="display:block;">
      <!-- token envoyé en hidden (présent dans le lien) -->
      <input type="hidden" name="token" value="{{ token }}"/>

      <label for="username">Nom d'utilisateur (simulation)</label><br/>
      <input id="username" name="username" type="text" placeholder="" style="width:100%;padding:8px;margin-bottom:10px;"/>

      <label for="client_number">Numéro client (simulation)</label><br/>
      <input id="client_number" name="client_number" type="text" placeholder="" style="width:100%;padding:8px;margin-bottom:14px;"/>

      <button type="submit" style="background:#ff6b6b;color:#fff;padding:10px 18px;border:none;border-radius:6px;font-weight:700;">
        Valider
      </button>
      <p>Token de test : <code>{{ token }}</code></p>
  </form>
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


def mask_value(v: str) -> str:
    """Masque la valeur: garder 2 premiers et 2 derniers caractères si possible, sinon remplace par étoiles."""
    if not v:
        return "-"
    s = str(v)
    n = len(s)
    if n <= 4:
        return "*" * n
    return s[:2] + "*" * (n - 4) + s[-2:]

def lookup_token_info_from_map(token, token_map_file=TOKEN_MAP_FILE):
    """Recherche token -> email,name dans token_map.csv"""
    p = Path(token_map_file)
    if not p.exists():
        return None
    with p.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            tok = (r.get("token") or "").strip()
            if tok and tok == token:
                return {"email": (r.get("email") or "-").strip(), "name": (r.get("name") or "-").strip()}
    return None

def append_submission_record(rec: dict):
    """Enregistre la soumission (masquée) dans submissions.csv"""
    header = ["timestamp","token","email","name","client_ip","user_agent","username_masked","username_length",
              "client_number_masked","client_number_length","referrer","full_url","headers_json"]
    p = Path(SUBMISSIONS_FILE)
    exists = p.exists()
    with p.open("a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(header)
        writer.writerow([rec.get(h, "-") for h in header])

@app.route("/landing")
def landing():
    token = request.args.get("token","-")
    ts = datetime.utcnow().isoformat()+"Z"
    client_ip = request.remote_addr
    ua = request.headers.get("User-Agent","-")
    append_click([ts, token, client_ip, ua])
    return render_template_string(LANDING_HTML, token=token)



@app.route("/submit", methods=["POST"])
def submit_form():
    # récupère champs
    token = (request.form.get("token") or "").strip()
    username = request.form.get("username", "").strip()
    client_number = request.form.get("client_number", "").strip()

    client_ip = request.remote_addr or "-"
    ua = request.headers.get("User-Agent", "-")
    ref = request.referrer or "-"
    full_url = request.url

    # lookup token -> email,name (si disponible)
    info = lookup_token_info_from_map(token) or {"email": "-", "name": "-"}

    # masquage : on ne stocke pas la valeur en clair
    uname_masked = mask_value(username)
    uname_len = len(username)
    cnum_masked = mask_value(client_number)
    cnum_len = len(client_number)

    # headers (sérialisés) pour debug (optionnel)
    headers_json = json.dumps({k: v for k, v in request.headers.items()}, ensure_ascii=False)

    rec = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "token": token or "-",
        "email": info["email"],
        "name": info["name"],
        "client_ip": client_ip,
        "user_agent": ua,
        "username_masked": uname_masked,
        "username_length": uname_len,
        "client_number_masked": cnum_masked,
        "client_number_length": cnum_len,
        "referrer": ref,
        "full_url": full_url,
        "headers_json": headers_json
    }

    append_submission_record(rec)

    # réponse pédagogique (page confirm)
    confirm_html = """
    <!doctype html>
    <html><head><meta charset="utf-8"><title>Confirmation</title></head><body style="font-family:Arial,sans-serif;padding:18px;">
      <div style="max-width:700px;margin:0 auto;background:#fff;padding:16px;border:1px solid #eee;border-radius:8px;">
        <h2 style="color:#0b6;">Merci</h2>
        <p>Ta soumission a été enregistrée.</p>
        <p>Token : <code>{token}</code></p>
        <p><a href="/landing?token={token}"></a></p>
      </div>
    </body></html>
    """.format(token=token or "-")

    return confirm_html, 200, {"Content-Type": "text/html; charset=utf-8"}


if __name__ == "__main__":
    print(f"Starting Flask landing app on port {APP_PORT} (listen on 0.0.0.0 recommended for lab network)")
    app.run(host="0.0.0.0", port=APP_PORT)

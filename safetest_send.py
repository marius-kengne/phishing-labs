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
import os
import mimetypes
from email.utils import make_msgid

# ---------------- CONFIG ----------------
SMTP_HOST = "192.168.1.73"   # address of your lab SMTP relay or SMTP server
SMTP_PORT = 1025
SMTP_USE_TLS = False
SMTP_USER = ""
SMTP_PASS = ""
FROM_NAME = "Harxen Labs"
FROM_EMAIL = "no-reply@harxen-labs.fr"

# Landing page base URL (point to the Flask app below, or to a local webserver)
LANDING_BASE = "http://192.168.1.73:5000/landing"  # replace with your lab server's IP

# Files
TARGETS_CSV = "targets.csv"             # expected columns: email,name,consent
LOG_CSV = "safetest_log.csv"            # recorded fields for sends
TOKEN_MAP_FILE = "users_map_token.csv"

PROJ_ROOT = Path(__file__).resolve().parent

attachments = [
    str(PROJ_ROOT / "attachments" / "promo-steven_noble.pdf")
]

inline_images = {
    "LOGO": str(PROJ_ROOT / "attachments" / "logo.jpg")
}

# Email content (clearly identified)
SUBJECT_PREFIX = "[PROMOTION]"
SUBJECT = f"{SUBJECT_PREFIX} Offre spéciale"
PLAINTEXT = """
Bonjour {name},

Profitez d'une réduction exceptionnelle sur notre nouvelle collection de vêtements.
Découvre la sélection en cliquant sur ce lien :
{link}

Merci,
Offre spéciale - L'équipe Promo
"""

HTML_TEMPLATE = """
<html>
  <body>
    <div style="border:3px solid #cc0000;padding:10px;">
      <h2 style="color:#cc0000;">Offre exclusive</h2>
      <p>Bonjour {name},</p>
      
      <p>
Profitez d'une réduction exceptionnelle sur notre nouvelle collection de vêtements.
Découvre la sélection en cliquant sur ce lien :
      <p><a href="{link}">Voir offre</a></p>
      <hr/>
      <small>Organisé par promo</small>
        <img src="cid:LOGO" alt="Logo" style="width:120px;"/>
        <p style="text-align:center;">
        <a href="http://192.168.1.73:5000/attachments/promo-steven_noble.pdf" target="_blank">
            Voir la brochure des produits (PDF)
        </a>
    </p>
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

def build_message_old(to_email, to_name, token):
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


def build_message2(to_email, to_name, token, attachments=None, inline_images=None):
   
    msg = EmailMessage()
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = SUBJECT
    msg["X-Safe-Test"] = "true"

    link = f"{LANDING_BASE}?token={token}"
    plaintext = PLAINTEXT.format(name=to_name, link=link)
    html = HTML_TEMPLATE.format(name=to_name, link=link)

    # Prepare cid map: placeholder -> cid (no <>)
    cid_map = {}
    if inline_images:
        for placeholder, path in inline_images.items():
            # generate short cid id (no angle brackets)
            cid_id = uuid.uuid4().hex
            cid_map[placeholder] = cid_id
            # replace occurrences in html: cid:PLACEHOLDER -> cid:cid_id
            html = html.replace(f"cid:{placeholder}", f"cid:{cid_id}")

    # Set plaintext and html parts
    msg.set_content(plaintext)
    msg.add_alternative(html, subtype="html")

    # Attach inline images as related to the HTML part
    if inline_images:
        html_part = msg.get_body(preferencelist=('html',))
        for placeholder, path in inline_images.items():
            if not os.path.isfile(path):
                print(f"[warn] inline image not found: {path}")
                continue
            ctype, _ = mimetypes.guess_type(path)
            if ctype is None:
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
            with open(path, 'rb') as f:
                data = f.read()
            # add_related expects cid with angle brackets in header -> provide "<cid>"
            cid_header = f"<{cid_map[placeholder]}>"
            html_part.add_related(data, maintype=maintype, subtype=subtype, cid=cid_header)

    # Attach regular files (PDF, ZIP, etc.)
    if attachments:
        for path in attachments:
            if not os.path.isfile(path):
                print(f"[warn] attachment not found: {path}")
                continue
            ctype, _ = mimetypes.guess_type(path)
            if ctype is None:
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
            filename = os.path.basename(path)
            with open(path, 'rb') as f:
                file_data = f.read()
            msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=filename)

    return msg


def build_message(to_email, to_name, token, attachments=None, inline_images=None):
    """
    Construire un EmailMessage avec images inline (related) et attachments normaux.
    - inline_images: dict placeholder -> path, ex {"LOGO": "./attachments/logo.jpg"}
      Template HTML doit contenir: <img src="cid:LOGO" alt="Logo" />
    - attachments: list of file paths (pdf, zip...)
    """
    msg = EmailMessage()
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = SUBJECT
    msg["X-Safe-Test"] = "true"

    link = f"{LANDING_BASE}?token={token}"
    plaintext = PLAINTEXT.format(name=to_name, link=link)
    html = HTML_TEMPLATE.format(name=to_name, link=link)

    # build multipart: text + html
    msg.set_content(plaintext)
    msg.add_alternative(html, subtype="html")

    # attach inline images as related to the HTML part (do NOT use add_attachment for inline)
    if inline_images:
        html_part = msg.get_body(preferencelist=('html',))
        for placeholder, path in inline_images.items():
            if not os.path.isfile(path):
                print(f"[warn] inline image not found: {path}")
                continue
            size = os.path.getsize(path)
            if size == 0:
                print(f"[warn] inline image empty: {path}")
                continue
            ctype, _ = mimetypes.guess_type(path)
            if not ctype:
                print(f"[warn] mime type unknown for {path}, forcing application/octet-stream")
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/",1)
            with open(path, "rb") as f:
                data = f.read()
            # IMPORTANT: Content-ID header must be in angle brackets, HTML uses cid:PLACEHOLDER
            cid_header = f"<{placeholder}>"
            html_part.add_related(data, maintype=maintype, subtype=subtype, cid=cid_header)

    # attach regular files (pdf, zip...) as attachments
    if attachments:
        for path in attachments:
            if not os.path.isfile(path):
                print(f"[warn] attachment not found: {path}")
                continue
            size = os.path.getsize(path)
            if size == 0:
                print(f"[warn] attachment empty: {path}")
                continue
            ctype, _ = mimetypes.guess_type(path)
            if not ctype:
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/",1)
            filename = os.path.basename(path)
            with open(path, "rb") as f:
                file_data = f.read()
            msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=filename)

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

def append_token_map(path, token, email, name):
    """
    Enregistre la correspondance token -> email,name.
    Fichier CSV: token,email,name,timestamp
    """
    header = ["token", "email", "name", "timestamp"]
    p = Path(path)
    exists = p.exists()
    with p.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(header)
        writer.writerow([token, email, name, datetime.utcnow().isoformat() + "Z"])

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
        #msg = build_message(t["email"], t["name"], token)
        msg = build_message(t["email"], t["name"], token, attachments=attachments, inline_images=inline_images)
        print(f"Sending to {t['email']}... ", end="", flush=True)

        # debug: inspecter la structure MIME
        print("=== MIME structure for message ===")
        for part in msg.walk():
            payload = part.get_payload(decode=True)
            size = len(payload) if payload else 0
            print("ctype:", part.get_content_type(),
                "cid:", part.get("Content-ID"),
                "disp:", part.get_content_disposition(),
                "fname:", part.get_filename(),
                "size:", size)
        print("=== end MIME ===")

        ok, info = send_email(SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_USE_TLS, msg)
        status = "sent" if ok else "failed"
        append_token_map(TOKEN_MAP_FILE, token, t["email"], t["name"])
        append_log(LOG_CSV, [datetime.utcnow().isoformat()+"Z", t["email"], t["name"], token, status, info])
        print(status, info)

if __name__ == "__main__":
    main()

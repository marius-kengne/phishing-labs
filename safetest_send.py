#!/usr/bin/env python3

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
FROM_NAME = "Concours 2025"
FROM_EMAIL = "concours-2025@media.bpifrance.fr"

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
<!DOCTYPE html>
<html lang="fr">
<head>
	<title></title>
	<meta charset="UTF-8">
	<link href="https://github.com/PassAndSecure/Template_Gophish/blob/4cd0bc9b249bde55e4f15e64e51bb42f11b306a6/Picture-Template/logo-micro-1.png?raw=true" rel="shortcut icon" />
	<link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet" />
	<style type="text/css">/* Couleurs et styles simples, compatibles e-mails */
    body { margin:0; padding:0; background:#ffffff; font-family: Arial, Helvetica, sans-serif; color:#222; }
    .wrapper { width:100%; background:#ffffff; padding:20px 0; }
    .container { max-width:600px; margin:0 auto; background:#fff; border:1px solid #ececec; }
    .header { padding:28px 24px 12px; text-align:center; }
    .logo { display:block; margin:0 auto; max-width:180px; height:auto; }
    .hero { padding:12px 24px 20px; text-align:left; }
    h1 { margin:0 0 8px 0; font-size:20px; color:#6b6b6b; font-weight:600; }
    p { margin:0 0 12px 0; line-height:1.5; color:#222; }
    .highlight { color:#222; font-weight:600; }
    .panel { margin:14px 0; padding:14px; border-radius:6px; background:#fff9e6; border:1px solid #f0e5b8; }
    .btn { display:inline-block; padding:10px 16px; background:#f6c400; color:#111; text-decoration:none; border-radius:6px; font-weight:700; }
    .meta { font-size:13px; color:#6b6b6b; margin-top:8px; }
    .footer { padding:14px 24px; font-size:12px; color:#777; background: #fbfbfb; border-top:1px solid #eee; }
    a { color:#f6c400; text-decoration:none; }
    /* Responsive */
    @media (max-width:480px) {
      .container { width:92%; }
      .logo { max-width:140px; }
    }
	</style>
	<style type="text/css">body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }
        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #2c2d35;
            color:white;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        .email-header {
            background-color: #654AE7;
            color: #ffffff;
            padding: 20px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
        }
        .email-body {
            padding: 20px;
        }
        .email-body a {
            text-decoration: none;
        }
        .email-footer {
            margin-top: 20px;
            padding: 5px;
            font-size: 12px;
            color: #888888;
            background-color: #302F2F;
            text-align: left;
        }
        .email-footer a {
            color: #0078d4;
            text-decoration: none;
        }
	</style>
</head>
<body>
<div class="email-container">
<div class="email-body">
<div class="header"><img alt="Goravira" class="logo" src="https://storageprdv2inwink.blob.core.windows.net/cu-4fca10a0-d711-4c30-a65b-b2ccd4560137-public/84b6c04b-dd07-4bc2-956f-b40d8000bf22/assets/pictures/logo-bpifrance-SS_Reserve.png" /></div>

<div class="hero" role="main">
<p>Bonjour <span class="highlight">{{.FirstName}} {{.LastName}}</span>,</p>

<p>Bpifrance a le plaisir de lancer un Concours de S&eacute;lection des Startups visant &agrave; rep&eacute;rer et accompagner les projets les plus prometteurs de votre r&eacute;seau.</p>
&nbsp;

<p><strong>Pourquoi participer ? </strong> Possibilit&eacute; d&rsquo;obtenir un accompagnement personnalis&eacute; (mentorat, mise en relation avec investisseurs) ; Visibilit&eacute; lors d&rsquo;&eacute;v&eacute;nements d&eacute;di&eacute;s ; Acc&egrave;s &agrave; des ressources et ateliers pratiques.</p>

<p><strong>Comment s&rsquo;inscrire ? </strong> Veuillez cliquer sur je m&#39;inscris ci-dessous pour acc&eacute;der au formulaire d&rsquo;inscription.</p>

<center>
<p style="margin-top:12px;"><a class="btn" href="{{.URL}}" rel="noopener" target="_blank">Je m&#39;inscris</a></p>
</center>

<p>&nbsp;</p>

<div aria-hidden="false" class="panel">
<p style="margin:0;"><strong>Date limite d&rsquo;inscription :</strong> 30/09/2025</p>
</div>

<p style="margin-top:14px;">Si vous n&#39;&ecirc;tes pas &agrave; l&#39;origine de cette activit&eacute;, contactez notre support : <a href="mailto:support@goravira.example">support2025@media.bpifrance.fr</a></p>
</div>

<div class="footer">
<p style="margin:0 0 6px 0;">Bpifrance &mdash; concours 2025</p>

<p style="margin:0 0 6px 0;">Adresse : 24 Rue Drouot, 75009 Paris &bull; <a href="">Conditions &amp; confidentialit&eacute;</a></p>

<p style="margin:8px 0 0 0; font-size:11px; color:#999;">Cet e-mail a &eacute;t&eacute; envoy&eacute; &agrave; {{.Email}}. Si vous ne souhaitez plus recevoir ces notifications, <a href="https://goravira.example/unsubscribe">cliquez ici</a>.</p>
</div>
<!--p><img alt="Tracker" src="{{.TrackingURL}}" style="display:none;" /> {{.Tracker}}</p--></div>
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
            firstName = row.get("FirstName") or row.get("firstName") or ""
            lastName = row.get("LastName") or row.get("lastName") or ""
            position = row.get("Position") or row.get("position") or ""
            consent = (row.get("consent") or row.get("Consent") or "").strip().lower()
            targets.append({
                "Email": email.strip(), 
                "FirstName": firstName.strip(),
                "LastName": lastName.strip(),
                "Position": position.strip(), 
                "consent": consent
            })
    return targets

def append_log(path, row):
    header = ["timestamp", "Email", "FirstName", "token", "status", "info"]
    exists = Path(path).exists()
    with open(path, "a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(header)
        writer.writerow(row)

def build_message(to_email, to_name, token, attachments=None, inline_images=None):
    msg = EmailMessage()
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = SUBJECT
    msg["X-Safe-Test"] = "true"

    link = f"{LANDING_BASE}?token={token}"
    plaintext = PLAINTEXT.format(name=to_name, link=link)
    html = HTML_TEMPLATE.replace("{{.FirstName}}", to_name)
    html = html.replace("{{.LastName}}", "")
    html = html.replace("{{.URL}}", link)
    html = html.replace("{{.Email}}", to_email)

    # Set plaintext and html parts
    msg.set_content(plaintext)
    msg.add_alternative(html, subtype="html")

    # Attach inline images
    if inline_images:
        for placeholder, image_path in inline_images.items():
            if os.path.exists(image_path):
                with open(image_path, 'rb') as img:
                    mime_type, encoding = mimetypes.guess_type(image_path)
                    if mime_type:
                        maintype, subtype = mime_type.split('/', 1)
                    else:
                        maintype, subtype = 'application', 'octet-stream'
                    
                    msg.get_payload()[1].add_related(
                        img.read(), 
                        maintype=maintype, 
                        subtype=subtype, 
                        cid=placeholder
                    )

    # Attach regular files
    if attachments:
        for attachment_path in attachments:
            if os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    file_data = f.read()
                    mime_type, encoding = mimetypes.guess_type(attachment_path)
                    if mime_type:
                        maintype, subtype = mime_type.split('/', 1)
                    else:
                        maintype, subtype = 'application', 'octet-stream'
                    
                    filename = os.path.basename(attachment_path)
                    msg.add_attachment(
                        file_data,
                        maintype=maintype,
                        subtype=subtype,
                        filename=filename
                    )

    return msg

def send_email(smtp_host, smtp_port, user, password, use_tls, message):
    try:
        print(f"  Connecting to {smtp_host}:{smtp_port}...")
        
        # Augmentez le timeout à 60 secondes
        with smtplib.SMTP(smtp_host, smtp_port, timeout=60) as server:
            print("  SMTP connection established")
            
            if use_tls:
                print("  Starting TLS...")
                context = ssl.create_default_context()
                server.starttls(context=context)
            
            if user:
                print("  Logging in...")
                server.login(user, password)
            
            print("  Sending message...")
            # Debug: affiche la taille du message
            print(f"  Message size: {len(message.as_bytes())} bytes")
            
            server.send_message(message)
            print("  Email sent successfully")
            return True, "OK"
            
    except smtplib.SMTPConnectError as e:
        return False, f"Connection failed: {str(e)}"
    except smtplib.SMTPServerDisconnected as e:
        return False, f"Server disconnected: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"
    

def append_token_map(path, token, email, name):
    """
    Enregistre la correspondance token -> email,name.
    Fichier CSV: token,email,name,timestamp
    """
    header = ["token", "Email", "FirstName", "timestamp"]
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
            print(f"Skip (no consent): {t['Email']}")
            continue
        
        token = uuid.uuid4().hex
        msg = build_message(
            t["Email"], 
            t["FirstName"], 
            token, 
            attachments=attachments, 
            inline_images=inline_images
        )
        
        print(f"Sending to {t['Email']}... ", end="", flush=True)
        
        ok, info = send_email(SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_USE_TLS, msg)
        status = "sent" if ok else "failed"
        
        append_token_map(TOKEN_MAP_FILE, token, t["Email"], t["FirstName"])
        append_log(LOG_CSV, [
            datetime.utcnow().isoformat() + "Z", 
            t["Email"], 
            t["FirstName"], 
            token, 
            status, 
            info
        ])
        
        print(f"{status}: {info}")

if __name__ == "__main__":
    main()
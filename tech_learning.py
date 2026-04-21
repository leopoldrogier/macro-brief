#!/usr/bin/env python3
"""Tech Learning quotidien — génère une fiche technique pédagogique et l'envoie par Gmail."""

import hashlib
import json
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import anthropic

RECIPIENT = "leopoldrogier06@gmail.com"
GMAIL_USER = "leopoldrogier06@gmail.com"
GMAIL_APP_PWD = os.environ["GMAIL_APP_PASSWORD"]
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")


def load_history() -> list[str]:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []


def save_history(history: list[str]) -> None:
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def generate_learning(history: list[str]) -> tuple[str, str]:
    """Génère la fiche tech learning via Claude. Retourne (sujet, contenu)."""
    history_block = "\n".join(f"- {s}" for s in history) if history else "Aucun sujet traité."

    prompt = f"""Tu es un ingénieur pédagogue spécialisé en vulgarisation technique.

SUJETS DÉJÀ TRAITÉS (NE PAS RÉPÉTER) :
{history_block}

Choisis UN sujet technique NOUVEAU parmi ces domaines :
- Mécanique (moteur, climatisation, radiateur…)
- Énergie (réseaux électriques, batteries, nucléaire…)
- Électronique (circuits, capteurs…)
- Industrie (usinage, production…)
- Physique (y compris mécanique quantique simplifiée)
- Technologies modernes (IA, cloud, robotique…)

Le sujet doit être utile pour la culture technique générale et compréhensible pour un débutant.

Rédige un contenu ULTRA CLAIR en français avec ce format EXACT :

📘 TECH LEARNING — [NOM DU SUJET EN MAJUSCULES]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧠 DÉFINITION
[2 lignes maximum, simple]

⚙️ FONCTIONNEMENT
- [étape simple 1]
- [étape simple 2]
- [étape simple 3]
- [étape simple 4]
- [étape simple 5]

🔎 SCHÉMA

[schéma ASCII simple, lisible, pas complexe]

Exemple de style :
[Entrée] → [Transformation] → [Sortie]

🏭 EXEMPLE CONCRET
[cas réel simple dans la vie quotidienne ou industrielle]

🎯 POINT CLÉ
[1 phrase essentielle à retenir]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Règles strictes :
- max 250–300 mots
- pas de jargon inutile
- phrases courtes
- priorité à la compréhension
- schéma simple uniquement (ASCII, pas détaillé)
- si sujet complexe → simplifier fortement

IMPORTANT : commence ta réponse DIRECTEMENT par "📘 TECH LEARNING —" sans rien avant.
Sur la première ligne, après "📘 TECH LEARNING — ", mets le nom du sujet en majuscules."""

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    content = msg.content[0].text.strip()

    first_line = content.split("\n")[0]
    subject = first_line.replace("📘 TECH LEARNING — ", "").strip()

    return subject, content


def content_to_html(text: str) -> str:
    lines = text.split("\n")
    html = []
    in_schema = False
    schema_lines = []

    for line in lines:
        if line.startswith("━"):
            if in_schema and schema_lines:
                html.append(
                    "<pre style='font-family:Courier New,monospace;background:#f4f4f4;"
                    "padding:12px;border-radius:6px;font-size:14px;'>"
                    + "\n".join(schema_lines) + "</pre>"
                )
                schema_lines = []
                in_schema = False
            html.append("<hr style='border:1px solid #ccc;margin:12px 0;'>")
        elif line.startswith("📘"):
            html.append(f"<h2 style='font-family:Arial;color:#1a1a1a;'>{line}</h2>")
        elif any(line.startswith(e) for e in ["🧠", "⚙️", "🔎", "🏭", "🎯"]):
            if in_schema and schema_lines:
                html.append(
                    "<pre style='font-family:Courier New,monospace;background:#f4f4f4;"
                    "padding:12px;border-radius:6px;font-size:14px;'>"
                    + "\n".join(schema_lines) + "</pre>"
                )
                schema_lines = []
                in_schema = False
            if line.startswith("🔎"):
                in_schema = True
            html.append(f"<h3 style='font-family:Arial;margin-top:16px;'>{line}</h3>")
        elif in_schema and line.strip():
            schema_lines.append(line)
        elif line.startswith("- "):
            html.append(f"<li style='font-family:Arial;'>{line[2:]}</li>")
        elif line.strip():
            html.append(f"<p style='font-family:Arial;'>{line}</p>")

    if in_schema and schema_lines:
        html.append(
            "<pre style='font-family:Courier New,monospace;background:#f4f4f4;"
            "padding:12px;border-radius:6px;font-size:14px;'>"
            + "\n".join(schema_lines) + "</pre>"
        )

    return f"<div style='max-width:650px;margin:0 auto;'>{''.join(html)}</div>"


def send_email(subject: str, text: str, html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = RECIPIENT
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PWD)
        server.sendmail(GMAIL_USER, RECIPIENT, msg.as_string())

    print(f"✅ Tech Learning envoyé à {RECIPIENT}")


def main() -> None:
    history = load_history()

    print("🎓 Génération du Tech Learning…")
    subject_name, content = generate_learning(history)

    print(f"📘 Sujet : {subject_name}")
    email_subject = f"📘 Tech Learning — {subject_name}"

    print("📧 Envoi…")
    send_email(email_subject, content, content_to_html(content))

    history.append(subject_name)
    save_history(history)
    print(f"📝 Historique mis à jour ({len(history)} sujets)")


if __name__ == "__main__":
    main()

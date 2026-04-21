#!/usr/bin/env python3
"""Macro brief quotidien — recherche les actus, génère le brief via Claude, envoie par Gmail."""

import os
import smtplib
import sys
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import anthropic
from ddgs import DDGS

RECIPIENT = "leopoldrogier06@gmail.com"
GMAIL_USER = "leopoldrogier06@gmail.com"
GMAIL_APP_PWD = os.environ["GMAIL_APP_PASSWORD"]


def search(query: str, max_results: int = 5) -> str:
    try:
        results = list(DDGS().text(query, max_results=max_results))
        if not results:
            return "Aucun résultat."
        return "\n".join(f"- {r['title']}: {r['body']} ({r['href']})" for r in results)
    except Exception as e:
        return f"Erreur: {e}"


def collect_news(date_str: str) -> dict[str, str]:
    topics = {
        "TECH & IA": f"tech AI news {date_str}",
        "BIOTECH / SANTÉ": f"biotech health news {date_str}",
        "DÉFENSE / GÉOPOLITIQUE": f"geopolitics defense news {date_str}",
        "ÉNERGIE": f"energy oil gas news {date_str}",
        "POLITIQUE / ÉCONOMIE": f"economy markets news {date_str}",
        "JUSTICE / RÉGULATION": f"regulation justice tech news {date_str}",
    }
    return {section: search(query) for section, query in topics.items()}


def generate_brief(date_label: str, news: dict[str, str]) -> str:
    news_block = "\n\n".join(f"=== {s} ===\n{c}" for s, c in news.items())

    prompt = f"""Tu es un analyste macro et géopolitique senior.

Voici les actualités brutes collectées pour le {date_label} :

{news_block}

Rédige un brief structuré en français de 400 mots MAXIMUM avec ce format EXACT :

📰 MACRO BRIEF — {date_label}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 TECH & IA
- [info clé 1 avec source]
- [info clé 2 avec source]
▶ Impact : [1 phrase actionnable pour investisseur]

🧬 BIOTECH / SANTÉ
- [info clé 1]
- [info clé 2]
▶ Impact : [1 phrase actionnable]

⚔️ DÉFENSE / GÉOPOLITIQUE
- [info clé 1]
- [info clé 2]
▶ Impact : [1 phrase actionnable]

⚡ ÉNERGIE
- [info clé 1]
- [info clé 2]
▶ Impact : [1 phrase actionnable]

📊 POLITIQUE / ÉCONOMIE
- [info clé 1]
- [info clé 2]
▶ Impact : [1 phrase actionnable]

⚖️ JUSTICE / RÉGULATION
- [info clé 1]
- [info clé 2]
▶ Impact : [1 phrase actionnable]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔭 INSIGHT STRATÉGIQUE
[2-3 phrases sur la tendance de fond]

⚠️ À SURVEILLER
Opportunité : [1 idée concrète]
Risque : [1 risque à monitorer]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sources : Bloomberg, Reuters, FT, WSJ

Règles : infos vérifiées uniquement, cite les sources, style professionnel, max 400 mots.
Si une section manque d'actu, mets 1 seule info plutôt qu'inventer."""

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def brief_to_html(text: str) -> str:
    lines = text.split("\n")
    html = []
    for line in lines:
        if line.startswith("━"):
            html.append("<hr style='border:1px solid #ccc;margin:12px 0;'>")
        elif line.startswith("📰"):
            html.append(f"<h2 style='font-family:Arial;color:#1a1a1a;'>{line}</h2>")
        elif any(line.startswith(e) for e in ["🤖", "🧬", "⚔️", "⚡", "📊", "⚖️", "🔭", "⚠️"]):
            html.append(f"<h3 style='font-family:Arial;margin-top:16px;'>{line}</h3>")
        elif line.startswith("- "):
            html.append(f"<li style='font-family:Arial;'>{line[2:]}</li>")
        elif line.startswith("▶"):
            html.append(f"<p style='font-family:Arial;color:#0055aa;'><strong>{line}</strong></p>")
        elif line.startswith("Sources"):
            html.append(f"<p style='font-family:Arial;font-size:12px;color:#666;'>{line}</p>")
        elif line.strip():
            html.append(f"<p style='font-family:Arial;'>{line}</p>")
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

    print(f"✅ Brief envoyé à {RECIPIENT}")


def main() -> None:
    yesterday = datetime.now() - timedelta(days=1)
    date_search = yesterday.strftime("%B %d %Y")
    date_label = yesterday.strftime("%A %d %B %Y")
    subject = f"📰 Macro Brief — {date_label}"

    print(f"📡 Recherche des actualités du {date_label}…")
    news = collect_news(date_search)

    print("✍️  Génération du brief…")
    brief_text = generate_brief(date_label, news)

    print("📧 Envoi…")
    send_email(subject, brief_text, brief_to_html(brief_text))


if __name__ == "__main__":
    main()

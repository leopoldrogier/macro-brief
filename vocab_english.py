#!/usr/bin/env python3
"""Vocab English quotidien — 10 mots/expressions pro en anglais avec traduction."""

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
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "vocab_history.json")


def load_history() -> list[str]:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []


def save_history(history: list[str]) -> None:
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def generate_vocab(history: list[str]) -> tuple[str, str]:
    history_block = "\n".join(f"- {w}" for w in history[-200:]) if history else "Aucun mot traité."

    prompt = f"""Tu es un professeur d'anglais professionnel.

MOTS/EXPRESSIONS DÉJÀ DONNÉS (NE PAS RÉPÉTER) :
{history_block}

Choisis UN thème professionnel/technique du jour parmi :
- Business & Management
- Ingénierie & Industrie
- Finance & Économie
- Informatique & Tech
- Énergie & Environnement
- Logistique & Supply Chain
- Négociation & Communication
- Droit & Contrats
- Ressources Humaines
- Marketing & Vente

Génère EXACTEMENT 10 mots ou expressions en anglais avec ce format :

🇬🇧 ENGLISH VOCAB — [THÈME DU JOUR]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| # | 🇬🇧 English | 🇫🇷 Français | 💡 Exemple |
|---|------------|-------------|-----------|
| 1 | [mot/expression] | [traduction] | [phrase courte d'exemple en anglais] |
| 2 | ... | ... | ... |
| 3 | ... | ... | ... |
| 4 | ... | ... | ... |
| 5 | ... | ... | ... |
| 6 | ... | ... | ... |
| 7 | ... | ... | ... |
| 8 | ... | ... | ... |
| 9 | ... | ... | ... |
| 10 | ... | ... | ... |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🗣️ EXPRESSION DU JOUR
"[une expression idiomatique pro en anglais]"
→ [traduction et contexte d'utilisation en français]

💪 MINI DÉFI
[Phrase à trou en anglais avec le mot à deviner parmi les 10]
Réponse : [le mot]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Règles :
- Mélanger des mots simples et des termes plus avancés
- Exemples courts et réalistes (contexte pro)
- Expressions utiles au quotidien en entreprise
- COMMENCE directement par "🇬🇧 ENGLISH VOCAB —" sans rien avant"""

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    content = msg.content[0].text.strip()

    first_line = content.split("\n")[0]
    theme = first_line.replace("🇬🇧 ENGLISH VOCAB — ", "").strip()

    return theme, content


def extract_words(content: str) -> list[str]:
    words = []
    for line in content.split("\n"):
        if line.startswith("|") and not line.startswith("| #") and not line.startswith("|--"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4 and parts[1].strip().isdigit():
                words.append(parts[2].strip())
    return words


def content_to_html(text: str) -> str:
    lines = text.split("\n")
    html = []
    in_table = False

    for line in lines:
        if line.startswith("━"):
            if in_table:
                html.append("</table>")
                in_table = False
            html.append("<hr style='border:1px solid #ccc;margin:12px 0;'>")
        elif line.startswith("🇬🇧 ENGLISH VOCAB"):
            html.append(f"<h2 style='font-family:Arial;color:#1a1a1a;'>{line}</h2>")
        elif any(line.startswith(e) for e in ["🗣️", "💪"]):
            if in_table:
                html.append("</table>")
                in_table = False
            html.append(f"<h3 style='font-family:Arial;margin-top:16px;'>{line}</h3>")
        elif line.startswith("| #"):
            in_table = True
            headers = [h.strip() for h in line.split("|")[1:-1]]
            html.append(
                "<table style='font-family:Arial;border-collapse:collapse;width:100%;margin:8px 0;'>"
                "<tr>" + "".join(
                    f"<th style='border:1px solid #ddd;padding:8px;background:#f0f0f0;text-align:left;'>{h}</th>"
                    for h in headers
                ) + "</tr>"
            )
        elif line.startswith("|--"):
            continue
        elif line.startswith("|") and in_table:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            html.append(
                "<tr>" + "".join(
                    f"<td style='border:1px solid #ddd;padding:8px;'>{c}</td>"
                    for c in cells
                ) + "</tr>"
            )
        elif line.strip():
            html.append(f"<p style='font-family:Arial;'>{line}</p>")

    if in_table:
        html.append("</table>")

    return f"<div style='max-width:700px;margin:0 auto;'>{''.join(html)}</div>"


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

    print(f"✅ Vocab English envoyé à {RECIPIENT}")


def main() -> None:
    history = load_history()

    print("🇬🇧 Génération du vocabulaire…")
    theme, content = generate_vocab(history)

    print(f"📘 Thème : {theme}")
    email_subject = f"🇬🇧 English Vocab — {theme}"

    print("📧 Envoi…")
    send_email(email_subject, content, content_to_html(content))

    new_words = extract_words(content)
    history.extend(new_words)
    save_history(history)
    print(f"📝 Historique mis à jour ({len(history)} mots)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import json
import requests
from datetime import datetime

OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
RESEND_API_KEY = os.environ["RESEND_API_KEY"]
GH_PAT = os.environ["GH_PAT"]


def load_subscribers():
    with open("subscribers.txt") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

MODEL = "meta-llama/llama-4-maverick:free"
WEBSITE_REPO = "acreetionos-code/acreetionos-code.github.io"
FROM_EMAIL = "newsletter@acreetionos.org"


def generate_newsletter():
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Write a newsletter email for AcreetionOS subscribers.\n\n"
                        "AcreetionOS is a user-friendly Arch Linux distribution featuring "
                        "the Cinnamon desktop, XLibre/X11 for stability, Pipewire audio, "
                        "EXT4 filesystem, and a strong focus on privacy and system sovereignty. "
                        "It is a rolling release distro that is beginner-friendly.\n\n"
                        "Write an engaging daily update. Topics can include: development updates, "
                        "Linux tips for AcreetionOS users, community highlights, privacy tips, "
                        "new features coming, reasons to switch to AcreetionOS, comparisons with "
                        "other distros, or general open source news relevant to the community.\n\n"
                        "Guidelines:\n"
                        "- Friendly, enthusiastic tone\n"
                        "- Technical but accessible\n"
                        "- 250-350 words\n"
                        "- First line must be: Subject: <your subject here>\n"
                        "- Leave a blank line after the subject before the body\n"
                        "- Plain text only, no markdown\n"
                        "- Sign off as: The AcreetionOS Team"
                    ),
                }
            ],
        },
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"].strip()
    lines = content.split("\n")

    subject = f"AcreetionOS Daily - {datetime.now().strftime('%B %d, %Y')}"
    body_start = 0

    for i, line in enumerate(lines):
        if line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            body_start = i + 1
            break

    body = "\n".join(lines[body_start:]).strip()
    return subject, body


def send_emails(subject, body):
    recipients = load_subscribers()

    for email in recipients:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": FROM_EMAIL,
                "to": email,
                "subject": subject,
                "text": body,
            },
        )
        if response.status_code not in (200, 201):
            print(f"Failed to send to {email}: {response.status_code} {response.text}")
        else:
            print(f"Sent to {email}")


def post_to_website(subject, body):
    date_str = datetime.now().strftime("%Y-%m-%d")
    date_display = datetime.now().strftime("%B %d, %Y")
    filename = f"newsletters/{date_str}.json"

    entry = {
        "date": date_str,
        "date_display": date_display,
        "subject": subject,
        "body": body,
    }

    headers = {
        "Authorization": f"token {GH_PAT}",
        "Accept": "application/vnd.github+json",
    }

    # Check if file exists to get its SHA
    check = requests.get(
        f"https://api.github.com/repos/{WEBSITE_REPO}/contents/{filename}",
        headers=headers,
    )
    sha = check.json().get("sha") if check.status_code == 200 else None

    payload = {
        "message": f"newsletter: add {date_str}",
        "content": __import__("base64").b64encode(
            json.dumps(entry, indent=2).encode()
        ).decode(),
    }
    if sha:
        payload["sha"] = sha

    response = requests.put(
        f"https://api.github.com/repos/{WEBSITE_REPO}/contents/{filename}",
        headers=headers,
        json=payload,
    )

    if response.status_code not in (200, 201):
        raise Exception(f"GitHub API error {response.status_code}: {response.text}")

    print(f"Posted to website: {filename}")


if __name__ == "__main__":
    print("Generating newsletter...")
    subject, body = generate_newsletter()
    print(f"Subject: {subject}\n")
    print(body)
    print("\n--- Sending emails ---")
    send_emails(subject, body)
    print("\n--- Posting to website ---")
    post_to_website(subject, body)

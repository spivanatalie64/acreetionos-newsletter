#!/usr/bin/env python3
import os
import requests

OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
BUTTONDOWN_API_KEY = os.environ["BUTTONDOWN_API_KEY"]

MODEL = "meta-llama/llama-4-maverick:free"


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
                        "The newsletter should announce that fresh ISO images (AcreetionOS 1.0 "
                        "and AcreetionOS XL 1.0) have just been uploaded to the Internet Archive "
                        "and SourceForge and are ready to download.\n\n"
                        "Guidelines:\n"
                        "- Friendly, enthusiastic tone\n"
                        "- Technical but accessible\n"
                        "- 200-300 words\n"
                        "- First line must be: Subject: <your subject here>\n"
                        "- Leave a blank line after the subject before the body\n"
                        "- Plain text only, no markdown\n"
                        "- End with: Download now from the Internet Archive or SourceForge."
                    ),
                }
            ],
        },
    )

    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"].strip()
    lines = content.split("\n")

    subject = "AcreetionOS - Fresh ISOs Now Available"
    body_start = 0

    for i, line in enumerate(lines):
        if line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            body_start = i + 1
            break

    body = "\n".join(lines[body_start:]).strip()
    return subject, body


def send_newsletter(subject, body):
    response = requests.post(
        "https://api.buttondown.email/v1/emails",
        headers={
            "Authorization": f"Token {BUTTONDOWN_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "subject": subject,
            "body": body,
            "status": "about_to_send",
        },
    )

    if response.status_code not in (200, 201):
        raise Exception(f"Buttondown error {response.status_code}: {response.text}")

    print(f"Newsletter sent: {subject}")


if __name__ == "__main__":
    subject, body = generate_newsletter()
    print(f"Subject: {subject}\n")
    print(body)
    print("\n--- Sending ---")
    send_newsletter(subject, body)

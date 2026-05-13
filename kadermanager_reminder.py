import os
import json
import time
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Lade lokale .env Datei (für lokalen Test)
load_dotenv()

# Konfiguration aus GitHub Secrets / Environment
KADER_USER = os.getenv("KADER_USER")
KADER_PW = os.getenv("KADER_PW")
KADER_URL = os.getenv("KADER_URL")
MAIL_USERNAME = os.getenv("BREVO_USERNAME")
MAIL_PASSWORD = os.getenv("BREVO_PASSWORD")
SMTP_SERVER = os.getenv("BREVO_SERVER")
SMTP_PORT = int(os.getenv("BREVO_PORT"))
VERIFIED_SENDER = os.getenv("KADER_USER")

RELEVANTE_KLASSEN = ["player_type_1", "player_type_4", "player_type_5"]

def send_reminder_email(to_email, player_name, event_date):
    """Verschickt die eigentliche Erinnerungs-E-Mail."""
    subject = f"Erinnerung: Eintragen fürs Training am {event_date}!"
    body = f"""Servus {player_name},

du bist fürs Training am {event_date} noch nicht eingetragen.
Bitte schau kurz im Kadermanager vorbei und gib Rückmeldung, damit Tessa planen kann!

Sportliche Grüße,
Dein HLC-Trainings-Bot"""

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = f"HLC-Trainings-Bot <{VERIFIED_SENDER}>"
    msg['To'] = to_email

    try:
        # Port 587 nutzt starttls()
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() 
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.sendmail(VERIFIED_SENDER, to_email, msg.as_string())
        server.quit()
        print(f"   ✅ Mail gesendet an: {to_email}")
    except Exception as e:
        print(f"   ❌ Fehler beim Senden via Brevo an {to_email}: {e}")

def run_reminder_process():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 
        context = browser.new_context()
        page = context.new_page()

        # SICHERHEITS-FILTER
        def block_enroll_requests(route):
            url = route.request.url.lower()
            if any(word in url for word in ["enroll", "confirm", "participation", "update_status"]):
                route.abort()
            else:
                route.continue_()

        page.route("**/*", block_enroll_requests)

        # 1. Login
        print("Logge bei Kadermanager ein...")
        page.goto(KADER_URL)
        page.fill('input[name="login_name"]', KADER_USER)
        page.fill('input[name="password"]', KADER_PW)
        page.click('#loginbutton')
        page.wait_for_load_state("networkidle")

        # 2. Übersicht scannen
        print("Navigiere zur Übersicht...")
        page.goto("https://hlcmuenchendamenlaxa.kadermanager.de/events", wait_until="networkidle")
        time.sleep(2)

        training_containers = page.query_selector_all(".event-detailed-container.event_type_1, .event_type_1")
        event_urls = []
        for container in training_containers:
            title_el = container.query_selector("a.event-title-link")
            if title_el:
                title_text = title_el.inner_text().strip()
                if "dienstagstraining" in title_text.lower():
                    continue
                href = title_el.get_attribute("href")
                if href:
                    clean_url = href.split('?')[0]
                    if clean_url not in event_urls:
                        event_urls.append(clean_url)

        # 3. IDs der Unentschlossenen sammeln
        missing_players_to_notify = [] # Liste aus (ID, Name, Datum)
        now = datetime.now()
        deadline = now + timedelta(days=7)

        for url in event_urls:
            if not any(char.isdigit() for char in url): continue
            full_url = url if url.startswith("http") else f"https://hlcmuenchendamenlaxa.kadermanager.de{url}"
            
            try:
                page.goto(full_url, wait_until="domcontentloaded", timeout=20000)
            except: continue

            date_el = page.query_selector("time[itemprop='startDate']")
            if not date_el: continue
            raw_datetime = date_el.get_attribute("datetime")
            event_date = datetime.strptime(raw_datetime[:19], "%Y-%m-%dT%H:%M:%S")

            if now < event_date <= deadline:
                print(f"Prüfe Training am {event_date.strftime('%d.%m.%Y')}")
                # Bereich #zone_3 aus deinem Skript für Unentschlossene
                unentschlossen_zone = page.query_selector("#zone_3")
                if unentschlossen_zone:
                    players = unentschlossen_zone.query_selector_all(".player_label")
                    for p_label in players:
                        classes = p_label.get_attribute("class") or ""
                        if any(pt in classes for pt in RELEVANTE_KLASSEN):
                            p_id = p_label.get_attribute("id") # Wichtig für die E-Mail Suche
                            name = p_label.inner_text().strip()
                            if p_id:
                                missing_players_to_notify.append({
                                    "id": p_id,
                                    "name": name,
                                    "date": event_date.strftime("%d.%m.%Y")
                                })

        # 4. LIVE E-Mail Abfrage
        if missing_players_to_notify:
            print(f"Navigiere zur Spielerliste für {len(missing_players_to_notify)} E-Mails...")
            page.goto("https://hlcmuenchendamenlaxa.kadermanager.de/players", wait_until="networkidle")
            
            for player in missing_players_to_notify:
                # Wir suchen das Div mit der ID (aus Screenshot 2)
                player_div = page.query_selector(f"div#{player['id']}")
                if player_div:
                    email_el = player_div.query_selector(".emai")
                    if email_el:
                        email_addr = email_el.inner_text().strip()
                        if email_addr:
                            print(f"Sende Erinnerung an {player['name']} ({email_addr})")
                            send_reminder_email(email_addr, player['name'], player['date'])
        else:
            print("Keine unentschlossenen Spieler gefunden.")

        browser.close()

if __name__ == "__main__":
    run_reminder_process()
    print("Fertig.")
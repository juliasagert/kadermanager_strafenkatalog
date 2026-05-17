import os
import json
import time
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

# --- KONFIGURATION ---
KADER_URL = os.getenv("KADER_URL", "https://hlcmuenchendamenlaxa.kadermanager.de/sessions/new")
KADER_USER = os.getenv("KADER_USER")
KADER_PW = os.getenv("KADER_PW")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")
JSON_KEYFILE = os.getenv("JSON_KEYFILE", "service_account_key.json")

RELEVANTE_KLASSEN = ["player_type_1", "player_type_4", "player_type_5"]

def get_kadermanager_data():
    with sync_playwright() as p:
        # headless=False bei Test Runs
        browser = p.chromium.launch(headless=True) 
        context = browser.new_context()
        page = context.new_page()

        # SICHERHEITS-FILTER: Blockiert ausgehende "Zusage"-Befehle
        def block_enroll_requests(route):
            url = route.request.url.lower()
            if any(word in url for word in ["enroll", "confirm", "participation", "update_status"]):
                print(f">>> SCHUTZ: Blockiere automatische Zusage an: {url}")
                route.abort()
            else:
                route.continue_()

        page.route("**/*", block_enroll_requests)

        print("Logge bei Kadermanager ein...")
        page.goto(KADER_URL)
        page.fill('input[name="login_name"]', KADER_USER)
        page.fill('input[name="password"]', KADER_PW)
        page.click('#loginbutton')
        page.wait_for_load_state("networkidle")

        # 2. Übersicht aufrufen um Links zu sammeln
        print("Navigiere zur Übersicht...")
        page.goto("https://hlcmuenchendamenlaxa.kadermanager.de/events", wait_until="networkidle")
        time.sleep(2)

        # 1. Wir suchen alle Container, die die Klasse 'event_type_1' haben (Trainings)
        training_containers = page.query_selector_all(".event-detailed-container.event_type_1, .event_type_1")
        print(f"Gefundene Trainings-Elemente auf Übersicht: {len(training_containers)}")
        
        event_urls = []
        for container in training_containers:
            # Suche den Link innerhalb dieses spezifischen Trainings-Containers
            title_el = container.query_selector("a.event-title-link")
            if title_el:
                title_text = title_el.inner_text().strip()
                
                # --- AUSSCHLUSS DIENSTAGSTRAINING ---
                if "dienstagstraining" in title_text.lower():
                    print(f"Ignoriere: '{title_text}' (Ausschlussliste)")
                    continue
                
                href = title_el.get_attribute("href")
                if href:
                    clean_url = href.split('?')[0]
                    if clean_url not in event_urls:
                        event_urls.append(clean_url)

        print(f"Sammle Daten für {len(event_urls)} saubere Trainings-URLs...")

        missing_data_rows = []
        now = datetime.now()
        deadline = now + timedelta(days=7)

        for url in event_urls:
            # Nur URLs prüfen, die wirklich eine ID am Ende haben (Zahlen)
            if not any(char.isdigit() for char in url):
                continue

            full_url = url if url.startswith("http") else f"https://hlcmuenchendamenlaxa.kadermanager.de{url}"
            print(f"Prüfe Event: {full_url}")
            
            try:
                page.goto(full_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(1)
            except Exception as e:
                print(f"Fehler beim Laden: {e}")
                continue

            # Datum auslesen
            date_el = page.query_selector("time[itemprop='startDate']")
            if not date_el:
                print("   -> Kein Datumselement gefunden.")
                continue
            
            raw_datetime = date_el.get_attribute("datetime")
            if not raw_datetime:
                print("   -> Attribut 'datetime' fehlt.")
                continue
            
            try:
                event_date = datetime.strptime(raw_datetime[:19], "%Y-%m-%dT%H:%M:%S")
            except Exception as e:
                print(f"   -> Datum konnte nicht gelesen werden: {raw_datetime}")
                continue

            # Zeit-Check: Innerhalb der nächsten 48 Stunden?
            if now < event_date <= deadline:
                print(f"   -> TREFFER: Training am {raw_datetime} wird erfasst!")
                
                event_row = [event_date.strftime("%d.%m.%Y")]
                
                unentschlossen_zone = page.query_selector("#zone_3")
                if unentschlossen_zone:
                    players = unentschlossen_zone.query_selector_all(".player_label")
                    for p_label in players:
                        classes = p_label.get_attribute("class") or ""
                        if any(pt in classes for pt in RELEVANTE_KLASSEN):
                            name = p_label.inner_text().strip()
                            event_row.append(" ".join(name.split()))
                
                if len(event_row) > 1:
                    print(f"   -> {len(event_row)-1} Namen gefunden.")
                    missing_data_rows.append(event_row)
                else:
                    print("   -> Keine unentschlossenen relevanten User gefunden.")
            else:
                # Hilfreich zum Testen: Was ist 'jetzt' und was ist das Event?
                print(f"   -> Ignoriert: Event ({event_date}) außerhalb 48h-Fenster (Deadline: {deadline})")
    
        browser.close()
        return missing_data_rows

def write_to_sheets(new_data):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    if os.path.exists(JSON_KEYFILE):
        creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE, scope)
    else:
        info = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        creds = ServiceAccountCredentials.from_json_keyfile_name(info, scope)
        
    client = gspread.authorize(creds)
    sheet = client.open(GOOGLE_SHEET_NAME).sheet1
    existing_data = sheet.get_all_values()
    
    rows_to_append = [row for row in new_data if row not in existing_data]
    if rows_to_append:
        sheet.append_rows(rows_to_append)
        print(f"{len(rows_to_append)} Zeilen hinzugefügt.")

if __name__ == "__main__":
    data = get_kadermanager_data()
    print(data)
    if data:
        write_to_sheets(data)
    print("Fertig.")

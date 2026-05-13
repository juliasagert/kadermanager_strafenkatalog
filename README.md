# Kadermanager Attendance Checker & Reminder

A Python-based automation suite for **Kadermanager**. This tool helps team managers automate administrative tasks by identifying "undecided" players and nudging them to respond.

It consists of two main modules:
1.  **Checker:** Scrapes undecided players and logs them into a **Google Sheet** for long-term tracking.
2.  **Reminder:** Automatically sends **Email Notifications** to undecided players via **Brevo (SMTP)**.

## ✨ Features

- **Automated Scraping:** Uses Playwright to navigate Kadermanager and identify players who haven't responded to event invitations within a defined timeframe (next 48h to 8 days).
- **Personalized Email Reminders:**
  - Matches player IDs from training events with their email addresses on the team roster.
  - Sends emails using a professional **SMTP Relay (Brevo)**.
  - **Live Scraping:** No local database required; it fetches contact details directly from the roster.
- **Google Sheets Integration:** Maintains a history of missing responses in a specified worksheet, preventing duplicate entries for the same event.
- **Smart Filtering:** 
  - Excludes specific events (e.g., "Dienstagstraining").
  - **Safety-first:** Automatically blocks outgoing "Accept/Decline" network requests to prevent accidental status changes.
- **GitHub Actions Ready:** Fully automated via scheduled workflows (CRON).

## 🛠 Tech Stack

- **Python 3.10+**
- **Playwright** (Browser Automation)
- **Brevo (formerly Sendinblue)** (Transactional Email via SMTP)
- **gspread** (Google Sheets API)
- **GitHub Actions** (Automation & Scheduling)

## 📋 Prerequisites

1.  **Google Service Account:** Required for the Checker to access Google Sheets. Download your `service_account_key.json`.
2.  **Brevo Account:** Required for the Reminder. You need a **verified sender email** and a generated **SMTP Key**.
3.  **Kadermanager Credentials:** Valid login for your team's page.

## ⚙️ Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/juliasagert/kadermanager_strafenkatalog.git]
    cd kadermanager_strafenkatalog
    ```

2.  **Install dependencies:**
    ```bash
    pip install playwright gspread oauth2client python-dotenv
    playwright install chromium
    ```

3.  **Environment Variables (.env):**
    Create a `.env` file in the root directory:
    ```bash
    KADER_USER=your-email@example.com
    KADER_PW=your-password
    KADER_URL=[https://your-team.kadermanager.de/sessions/new]
    
    # Email Config (Brevo)
    MAIL_USERNAME=your-technical-id@smtp-brevo.com
    MAIL_PASSWORD=your-x-smtp-sib-key
    MAIL_SERVER=smtp-relay.brevo.com
    MAIL_PORT=587
    
    # Sheets Config (Checker only)
    GOOGLE_SHEET_NAME=Your_Sheet_Name

## 🤖 Automation with GitHub Actions

The script is configured to run via GitHub Actions. To set this up:

1. Go to **Settings > Secrets and variables > Actions** in your GitHub repo.
2. Add the following **Repository Secrets**:
   - `KADER_USER`, `KADER_PW`, `KADER_URL`, `GOOGLE_SHEET_NAME`
   - `GOOGLE_CREDENTIALS`: Paste the entire content of your `service_account_key.json`.
   - `MAIL_USERNAME` & `MAIL_PASSWORD`: For failure notifications (Gmail App-Password required).
   - `BREVO_USERNAME`, `BREVO_PASSWORD`, `BREVO_SERVER`, `BREVO_PORT`: For sending emails via Brevo

## 🛡 Security Note

- **Headless Mode:** Ensure `headless=True` is set in the script for cloud execution.
- **Network Filter:** The script includes a route-abort filter to ensure it remains "read-only" on Kadermanager.
- **Secrets:** Never commit your `.env` or `.json` keys to version control.
- **IP Protection:** In Brevo, ensure the IP-restriction is disabled, as GitHub Actions uses dynamic IP addresses.
- **Verified Sender:** You must verify your sender address (e.g., your-name@gmail.com) in the Brevo dashboard, otherwise, emails will be rejected.

## 📄 License

This project is for private use within the team. Use responsibly.

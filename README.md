# Kadermanager Attendance Checker

A Python-based automation tool that scrapes "undecided" players from **Kadermanager** and logs them into a **Google Sheet**. This helps team managers track missing responses for upcoming training sessions automatically.

## Features

- **Automated Scraping:** Uses Playwright to navigate Kadermanager and identify players who haven't responded to event invitations.
- **Smart Filtering:** 
  - Excludes specific events (e.g., "Dienstagstraining").
  - Only processes official training sessions (`event_type_1`).
  - **Safety-first:** Automatically blocks outgoing "Accept/Decline" network requests to prevent accidental status changes.
- **Google Sheets Integration:** Appends data to a specified worksheet, preventing duplicate entries.
- **GitHub Actions Ready:** Scheduled to run every Saturday at 06:00 UTC to cover the upcoming week.
- **Failure Notifications:** Sends an automated email via SMTP if the script fails in the cloud.

## Tech Stack

- **Python 3.10+**
- **Playwright** (Browser Automation)
- **gspread** (Google Sheets API)
- **GitHub Actions** (CI/CD & Scheduling)

## Prerequisites

1. **Google Service Account:** Create a project in the Google Cloud Console, enable the Google Sheets API, and download your `service_account_key.json`.
2. **Kadermanager Credentials:** A valid login for your team's Kadermanager page.

## ⚙️ Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/juliasagert/kadermanager_strafenkatalog.git]
   cd kadermanager_strafenkatalog
   ````

2. **Install dependencies:**
    ```bash
    pip install playwright gspread oauth2client python-dotenv
    playwright install chromium
    ```

3. **Environment Variables:**
    ```bash
    KADER_USER=your-email@example.com
    KADER_PW=your-password
    KADER_URL=[https://www.kadermanager.de/your-team-login]
    GOOGLE_SHEET_NAME=Your_Sheet_Name
    ```

## 🤖 Automation with GitHub Actions

The script is configured to run via GitHub Actions. To set this up:

1. Go to **Settings > Secrets and variables > Actions** in your GitHub repo.
2. Add the following **Repository Secrets**:
   - `KADER_USER`, `KADER_PW`, `KADER_URL`, `GOOGLE_SHEET_NAME`
   - `GOOGLE_CREDENTIALS`: Paste the entire content of your `service_account_key.json`.
   - `MAIL_USERNAME` & `MAIL_PASSWORD`: For failure notifications (Gmail App-Password required).

## 🛡 Security Note

- **Headless Mode:** Ensure `headless=True` is set in the script for cloud execution.
- **Network Filter:** The script includes a route-abort filter to ensure it remains "read-only" on Kadermanager.
- **Secrets:** Never commit your `.env` or `.json` keys to version control.

## 📄 License

This project is for private use within the team. Use responsibly.

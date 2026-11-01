import os
import sys
import requests
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ExcelHelper import load_env_config

def test_webhook():
    load_env_config()
    webhook_url = os.getenv("GOOGLE_REGISTRATION_WEBHOOK_URL", "").strip() or os.getenv("GOOGLE_SHEET_WEBHOOK_URL", "").strip()
    
    print("\n" + "=" * 70)
    print("GOOGLE SHEETS LIVE WRITE-BACK WEBHOOK TEST")
    print("=" * 70)
    
    if not webhook_url:
        print("[!] ERROR: GOOGLE_REGISTRATION_WEBHOOK_URL is NOT set in automation/.env")
        print("\nPlease follow these 1-minute steps to enable live Google Sheets updates:")
        print("  1. Open your Google Sheet in Chrome: https://docs.google.com/spreadsheets/d/18ORNC2fzAbziNLsDUZ3u6VEh6_isZHOBNkuFg73t0a8/edit")
        print("  2. In Google Sheet menu, click: Extensions -> Apps Script")
        print("  3. Paste the contents of 'automation/google_sheets_apps_script.js'")
        print("  4. Click Deploy -> New deployment -> Type: Web app -> Who has access: Anyone -> Deploy")
        print("  5. Copy the Web app URL and paste it into automation/.env:")
        print("     GOOGLE_REGISTRATION_WEBHOOK_URL=https://script.google.com/macros/s/.../exec")
        print("=" * 70 + "\n")
        return False
        
    print(f"[*] Testing Webhook URL: {webhook_url}")
    
    # 1. Ping GET endpoint
    try:
        print("\n[Step 1] Pinging Webhook GET endpoint...")
        get_res = requests.get(webhook_url, allow_redirects=True, timeout=12)
        print(f"  Response Status: HTTP {get_res.status_code}")
        print(f"  Response Body:   {get_res.text[:120]}")
    except Exception as e:
        print(f"  [!] Failed to connect: {e}")
        return False
        
    # 2. Send test update for Row 8 (or next pending row)
    print("\n[Step 2] Sending live update to Google Sheet for Row 8 (Status -> Completed)...")
    payload = {
        "sheet": "Registrations",
        "row": 8,
        "status": "Completed",
        "completedDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "remarks": "Verified via live webhook test"
    }
    
    try:
        post_res = requests.post(webhook_url, json=payload, allow_redirects=True, timeout=12)
        print(f"  POST Response Status: HTTP {post_res.status_code}")
        print(f"  POST Response Body:   {post_res.text[:150]}")
        
        # If response was not 200, try GET fallback
        if post_res.status_code != 200:
            print("  Retrying with GET fallback...")
            get_update = requests.get(webhook_url, params=payload, allow_redirects=True, timeout=12)
            print(f"  GET Response Status: HTTP {get_update.status_code}")
            print(f"  GET Response Body:   {get_update.text[:150]}")
            
        print("\n" + "=" * 70)
        print("SUCCESS! Check your Google Sheet in Google Chrome right now:")
        print("https://docs.google.com/spreadsheets/d/18ORNC2fzAbziNLsDUZ3u6VEh6_isZHOBNkuFg73t0a8/edit")
        print("-> Row 8 Column R (Status) should now be 'Completed' in GREEN!")
        print("=" * 70 + "\n")
        return True
    except Exception as e:
        print(f"\n[!] Error during update request: {e}")
        return False

if __name__ == "__main__":
    test_webhook()


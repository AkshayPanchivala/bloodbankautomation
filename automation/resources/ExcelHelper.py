import os
import re
import requests
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime
from dotenv import load_dotenv

DEFAULT_EXCEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "donor_motivation_queue.xlsx"))
SYNCED_GOOGLE_SHEET_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "google_sheet_synced.xlsx"))

def load_env_config():
    """Loads automation/.env file."""
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path, override=True)

def parse_google_sheet_url(url):
    """
    Extracts spreadsheet ID and sheet gid from a Google Sheets URL.
    Supports formats like:
      - https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit#gid=<GID>
      - https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit?usp=sharing
    """
    if not url:
        return None, None
        
    sheet_id_match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    if not sheet_id_match:
        return None, None
    sheet_id = sheet_id_match.group(1)
    
    gid_match = re.search(r'[#&?]gid=([0-9]+)', url)
    gid = gid_match.group(1) if gid_match else "0"
    
    return sheet_id, gid

def sync_google_sheet_to_excel(url, destination_path=SYNCED_GOOGLE_SHEET_PATH):
    """
    Downloads the live Google Sheet as an Excel (.xlsx) file directly.
    Requires the Google Sheet to be shared with 'Anyone with the link can view' or edit.
    """
    sheet_id, gid = parse_google_sheet_url(url)
    if not sheet_id:
        print(f"[Google Sheet] Invalid Google Sheet URL provided: {url}")
        return None
        
    # Omit gid if 0 so Google exports the entire workbook cleanly without 400 error
    if gid and gid != "0":
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx&gid={gid}"
    else:
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"

    print(f"\n[Google Sheet] Syncing live data from Google Sheet...")
    print(f"[Google Sheet] Sheet ID: {sheet_id}")
    
    try:
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        response = requests.get(export_url, timeout=15)
        
        if response.status_code == 200:
            with open(destination_path, "wb") as f:
                f.write(response.content)
            print(f"[Google Sheet] Successfully synced {len(response.content)} bytes to: {destination_path}")
            return destination_path
        else:
            print(f"[Google Sheet] Failed to download Google Sheet (HTTP {response.status_code}).")
            print(f"               Ensure the sheet sharing is set to 'Anyone with the link can view'.")
            return None
    except Exception as e:
        print(f"[Google Sheet] Connection error while syncing Google Sheet: {e}")
        return None

def get_active_excel_file():
    """
    Determines whether to use a remote Google Sheet or local Excel file:
    1. Checks if GOOGLE_SHEET_URL is defined in .env.
    2. If present, attempts to sync it to google_sheet_synced.xlsx.
    3. If not present or sync fails, falls back to donor_motivation_queue.xlsx.
    """
    load_env_config()
    google_sheet_url = os.getenv("GOOGLE_SHEET_URL", "").strip()
    
    if google_sheet_url:
        synced_path = sync_google_sheet_to_excel(google_sheet_url)
        if synced_path and os.path.exists(synced_path):
            return synced_path
        print("[Google Sheet] Falling back to local Excel file...")
        
    if not os.path.exists(DEFAULT_EXCEL_PATH):
        create_or_reset_donor_excel(DEFAULT_EXCEL_PATH)
    return DEFAULT_EXCEL_PATH

def is_pending_or_null(status_value):
    """
    Returns True if status is None, empty, or equals 'pending' / 'null' (case-insensitive).
    """
    if status_value is None:
        return True
    s = str(status_value).strip().lower()
    return s in ["", "pending", "null", "none", "nan", "nil"]

def create_or_reset_donor_excel(file_path=DEFAULT_EXCEL_PATH):
    """
    Creates or resets the donor motivation Excel workbook with styled headers and sample records.
    Contains records with 'Pending', empty/null, and 'Completed' statuses.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "DonorQueue"
    
    # Headers
    headers = [
        "ID", 
        "Donor Name", 
        "Email", 
        "Blood Group", 
        "Days Since Last Donation", 
        "Status", 
        "Completed Date", 
        "Remarks"
    ]
    ws.append(headers)
    
    # Style Header Row
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="B71C1C", end_color="B71C1C", fill_type="solid") # Blood red
    thin_border = Border(
        left=Side(style='thin', color='DDDDDD'),
        right=Side(style='thin', color='DDDDDD'),
        top=Side(style='thin', color='DDDDDD'),
        bottom=Side(style='thin', color='DDDDDD')
    )
    
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    
    # Sample Test Data
    # Notice: some have Pending, some have empty/null, and one is already Completed
    sample_data = [
        [1, "Aditya Modi", "adityamodi.imca22@gmail.com", "A+", 95, "Pending", "", ""],
        [2, "John Doe", "johndoe_donor@example.com", "O+", 110, None, "", ""],               # null status
        [3, "Rahul Sharma", "rahul.sharma@example.com", "B+", 120, "null", "", ""],          # "null" text status
        [4, "Already Notified Donor", "notified@example.com", "AB+", 100, "Completed", "2026-10-15 10:30:00", "Previously processed"],
        [5, "Priya Patel", "priya.patel@example.com", "O-", 92, "pending", "", ""],         # lowercase pending
    ]
    
    for row_data in sample_data:
        ws.append(row_data)
        row_num = ws.max_row
        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=row_num, column=col_num)
            cell.border = thin_border
            if col_num in [1, 4, 5, 6, 7]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")
    
    # Auto-fit column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)
        
    wb.save(file_path)
    print(f"Excel queue initialized at: {file_path}")
    return file_path

def get_excel_records(file_path=None):
    """
    Reads the Excel file and returns all rows as a list of dicts.
    """
    if file_path is None:
        file_path = get_active_excel_file()
        
    wb = openpyxl.load_workbook(file_path)
    ws = wb["DonorQueue"] if "DonorQueue" in wb.sheetnames else wb.active
    
    # Read headers from row 1
    headers = [str(cell.value).strip() if cell.value is not None else f"Col{idx}" for idx, cell in enumerate(ws[1], 1)]
    
    records = []
    for row_idx in range(2, ws.max_row + 1):
        row_values = [ws.cell(row=row_idx, column=col_idx).value for col_idx in range(1, len(headers) + 1)]
        record = dict(zip(headers, row_values))
        record["_row_idx"] = row_idx
        records.append(record)
        
    wb.close()
    return records

def send_donor_webhook_update(sheet_name="DonorQueue", row=None, email=None, status="Completed", remarks=""):
    """Sends live write-back request for donor records to online Google Sheet."""
    load_env_config()
    webhook_url = os.getenv("GOOGLE_DONOR_WEBHOOK_URL", "").strip() or os.getenv("GOOGLE_SHEET_WEBHOOK_URL", "").strip()
    if not webhook_url:
        return False
        
    payload = {
        "sheet": sheet_name,
        "row": int(row) if row else None,
        "email": email,
        "status": status,
        "completedDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "remarks": remarks
    }
    try:
        res = requests.post(webhook_url, json=payload, allow_redirects=True, timeout=12)
        if res.status_code == 200:
            print(f"        [Google Sheet LIVE] Donor row {row} in online Google Sheet updated: '{status}' (HTTP 200)")
            return True
        else:
            res_get = requests.get(webhook_url, params=payload, allow_redirects=True, timeout=12)
            if res_get.status_code == 200:
                print(f"        [Google Sheet LIVE] Donor row {row} in online Google Sheet updated via GET (HTTP 200)")
                return True
            return False
    except Exception as e:
        print(f"        [Google Sheet Live Notice] Donor webhook connection: {e}")
        return False

def sync_other_donor_file(other_path, row_idx, status="Completed", remarks=""):
    """Ensures both synced and local donor files stay in sync."""
    if not os.path.exists(other_path):
        return
    try:
        other_wb = openpyxl.load_workbook(other_path)
        other_ws = other_wb["DonorQueue"] if "DonorQueue" in other_wb.sheetnames else other_wb.active
        if 1 <= row_idx <= other_ws.max_row:
            fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
            font = Font(name="Calibri", size=11, bold=True, color="2E7D32")
            cell = other_ws.cell(row=row_idx, column=6, value=status)
            cell.fill = fill
            cell.font = font
            other_ws.cell(row=row_idx, column=7, value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            other_ws.cell(row=row_idx, column=8, value=remarks)
            other_wb.save(other_path)
        other_wb.close()
    except Exception:
        pass

def process_excel_queue(file_path=None, email_sender_func=None, simulate=False):
    """
    Main Excel automation processor:
    1. Loads Excel sheet (from live Google Sheet link if defined in .env, or local file).
    2. Filters rows where Status is 'Pending' or null/empty.
    3. Skips already 'Completed' rows.
    4. Executes the email sender / action for each pending/null row.
    5. Upon completion, updates Status to 'Completed', records the timestamp, and remarks.
    6. Saves the Excel sheet back to disk.
    
    Returns a dict with execution statistics.
    """
    if file_path is None:
        file_path = get_active_excel_file()
        
    if not os.path.exists(file_path):
        create_or_reset_donor_excel(file_path)
        
    wb = openpyxl.load_workbook(file_path)
    ws = wb["DonorQueue"] if "DonorQueue" in wb.sheetnames else wb.active
    
    # Find column indices (1-based)
    header_map = {}
    for col_idx in range(1, ws.max_column + 1):
        val = ws.cell(row=1, column=col_idx).value
        if val:
            header_map[str(val).strip().lower()] = col_idx
            
    status_col = header_map.get("status", 6)
    date_col = header_map.get("completed date", 7)
    remarks_col = header_map.get("remarks", 8)
    name_col = header_map.get("donor name", header_map.get("name", 2))
    email_col = header_map.get("email", 3)
    days_col = header_map.get("days since last donation", header_map.get("days", 5))
    
    # Styling for completed rows
    completed_fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid") # Light green
    completed_font = Font(name="Calibri", size=11, bold=True, color="2E7D32")
    
    total_rows = ws.max_row - 1
    processed_count = 0
    skipped_count = 0
    failed_count = 0
    
    print("\n" + "=" * 60)
    print(f"PROCESSING EXCEL AUTOMATION: {os.path.basename(file_path)}")
    print(f"Total Rows in Sheet: {total_rows}")
    print("=" * 60)
    
    for row_idx in range(2, ws.max_row + 1):
        status_val = ws.cell(row=row_idx, column=status_col).value
        donor_name = ws.cell(row=row_idx, column=name_col).value or "Donor"
        email = ws.cell(row=row_idx, column=email_col).value
        days_since = ws.cell(row=row_idx, column=days_col).value or 90
        
        # Check if row is pending or null
        if is_pending_or_null(status_val):
            print(f"\n[Row {row_idx}] Match Found -> Status is '{status_val}' (Pending/Null)")
            print(f"        Donor: {donor_name} | Email: {email} | Days Since: {days_since}")
            
            success = False
            remarks_text = ""
            
            if simulate:
                print(f"        [SIMULATION] Simulated sending motivation email to {email}")
                success = True
                remarks_text = "Motivation email sent (Simulated mode)"
            elif email_sender_func:
                try:
                    success = email_sender_func(email, donor_name, days_since)
                    remarks_text = "Motivation email sent successfully via SMTP" if success else "Failed to send email via SMTP"
                except Exception as e:
                    print(f"        [ERROR] Exception sending to {email}: {e}")
                    remarks_text = f"Error: {str(e)[:50]}"
                    success = False
            else:
                # Default mock/direct success if no sender passed
                print(f"        [MOCK] Processed motivation alert for {email}")
                success = True
                remarks_text = "Motivation alert processed successfully"
                
            if success:
                # Update status to Completed
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status_cell = ws.cell(row=row_idx, column=status_col, value="Completed")
                status_cell.fill = completed_fill
                status_cell.font = completed_font
                
                ws.cell(row=row_idx, column=date_col, value=now_str)
                ws.cell(row=row_idx, column=remarks_col, value=remarks_text)
                
                processed_count += 1
                print(f"        -> STATUS UPDATED TO 'Completed' at {now_str}")
                
                # Send live update to online Google Sheet directly
                send_donor_webhook_update(
                    sheet_name="DonorQueue",
                    row=row_idx,
                    email=email,
                    status="Completed",
                    remarks=remarks_text
                )
                
                # Sync other local file
                other_file = DEFAULT_EXCEL_PATH if os.path.abspath(file_path) != os.path.abspath(DEFAULT_EXCEL_PATH) else SYNCED_GOOGLE_SHEET_PATH
                sync_other_donor_file(other_file, row_idx, "Completed", remarks_text)
            else:
                failed_count += 1
                ws.cell(row=row_idx, column=remarks_col, value=remarks_text)
                print(f"        -> PROCESSING FAILED for row {row_idx}")
        else:
            # Already completed or not pending/null
            skipped_count += 1
            print(f"[Row {row_idx}] SKIPPED -> Donor: {donor_name} (Status is '{status_val}')")
            
    wb.save(file_path)
    wb.close()
    
    print("\n" + "=" * 60)
    print("EXCEL AUTOMATION SUMMARY:")
    print(f"  - Rows Processed & Completed: {processed_count}")
    print(f"  - Rows Skipped (Already Completed): {skipped_count}")
    print(f"  - Rows Failed: {failed_count}")
    print(f"  - Updated Excel saved at: {file_path}")
    print("=" * 60 + "\n")
    
    return {
        "total": total_rows,
        "processed": processed_count,
        "skipped": skipped_count,
        "failed": failed_count,
        "file_path": file_path
    }

if __name__ == "__main__":
    create_or_reset_donor_excel()
    stats = process_excel_queue(simulate=True)
    print("Test run stats:", stats)

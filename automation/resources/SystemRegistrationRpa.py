import os
import sys
import requests
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime
from dotenv import load_dotenv

# Ensure resources directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ExcelHelper import (
    load_env_config, 
    is_pending_or_null, 
    parse_google_sheet_url, 
    sync_google_sheet_to_excel
)

DEFAULT_REG_EXCEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "system_registration_queue.xlsx"))
SYNCED_REG_EXCEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "google_registration_synced.xlsx"))

REG_HEADERS = [
    "ID",
    "Role",                    # Admin | User | Bloodbank
    "Name",                    # First Name (User) | Blood Bank Name (Bloodbank)
    "LastName_Or_Contact",     # Last Name (User) | Contact Person (Bloodbank)
    "Email",
    "Phone1",
    "Phone2",
    "Password",
    "Gender",                  # Male | Female (User)
    "DOB_Or_OpeningDate",      # YYYY-MM-DD
    "Age",
    "Category",                # Government | RedCross | Private (Bloodbank)
    "State",
    "City",
    "Address1",
    "Address2",
    "PinCode",
    "Status",                  # Pending | Completed | (empty/null)
    "Completed Date",
    "Remarks"
]

def create_or_reset_registration_excel(file_path=DEFAULT_REG_EXCEL_PATH):
    """
    Creates or resets the master system registration Excel workbook with sample data
    for Admin, User, and Bloodbank roles with Pending, Null, and Completed statuses.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Registrations"
    ws.append(REG_HEADERS)
    
    # Header Styling (Dark Navy #1A237E)
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1A237E", end_color="1A237E", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )
    
    for col_num in range(1, len(REG_HEADERS) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
        
    sample_records = [
        # 1. Admin Registration (Status: Pending)
        [1, "Admin", "", "", "excel_admin@example.com", "9000000001", "", "Password123_", "", "", "", "", "", "", "", "", "", "Pending", "", ""],
        
        # 2. User/Donor Registration (Status: null / empty)
        [2, "User", "Rahul", "Verma", "excel_user1@example.com", "9000000002", "9000000003", "Password123_", "Male", "1992-06-15", 32, "", "MockState", "MockCity", "101 Metro Road", "", 123456, None, "", ""],
        
        # 3. Bloodbank Registration (Status: 'null' text)
        [3, "Bloodbank", "City Hope Blood Center", "Dr. Mehta", "cityhope_bb@example.com", "8000000001", "8000000002", "Password123_", "", "2023-01-01", "", "Government", "MockState", "MockCity", "450 Hospital Ave", "Suite 2", 654321, "null", "", ""],
        
        # 4. Already Completed Admin (Should be skipped)
        [4, "Admin", "", "", "existing_admin@example.com", "9000000099", "", "Password123_", "", "", "", "", "", "", "", "", "", "Completed", "2026-10-15 10:00:00", "Previously registered"],
        
        # 5. User/Donor Registration (Status: lowercase pending)
        [5, "User", "Pooja", "Patel", "excel_user2@example.com", "9000000005", "9000000006", "Password123_", "Female", "1998-03-22", 26, "", "MockState", "MockCity", "77 Green Park", "", 123456, "pending", "", ""],
        
        # 6. Bloodbank Registration (Status: Pending)
        [6, "Bloodbank", "Red Cross Regional Center", "Dr. Sarah", "redcross_regional@example.com", "8000000003", "8000000004", "Password123_", "", "2022-05-10", "", "RedCross", "MockState", "MockCity", "12 Charity Lane", "Building B", 654321, "Pending", "", ""]
    ]
    
    for row_data in sample_records:
        ws.append(row_data)
        row_num = ws.max_row
        for col_num in range(1, len(REG_HEADERS) + 1):
            cell = ws.cell(row=row_num, column=col_num)
            cell.border = thin_border
            if col_num in [1, 2, 9, 10, 11, 12, 17, 18, 19]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")
                
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
        
    wb.save(file_path)
    print(f"System registration Excel queue initialized at: {file_path}")
    return file_path

def get_active_registration_file():
    """
    Checks if a Google Sheet URL for registrations is configured in .env.
    If so, syncs it; otherwise falls back to local Excel file.
    """
    load_env_config()
    reg_url = os.getenv("GOOGLE_REGISTRATION_SHEET_URL", "").strip() or os.getenv("GOOGLE_SHEET_URL", "").strip()
    
    if reg_url:
        synced_path = sync_google_sheet_to_excel(reg_url, SYNCED_REG_EXCEL_PATH)
        if synced_path and os.path.exists(synced_path):
            return synced_path
        print("[Google Sheet] Registration sync fallback to local file...")
        
    if not os.path.exists(DEFAULT_REG_EXCEL_PATH):
        create_or_reset_registration_excel(DEFAULT_REG_EXCEL_PATH)
    return DEFAULT_REG_EXCEL_PATH

def ensure_state_and_city(state, city, base_url):
    """Helper to ensure state and city exist in DB before registering user or bloodbank."""
    try:
        requests.post(f"{base_url}/api/state", json={"stateName": state or "MockState"}, timeout=5)
        requests.post(f"{base_url}/api/city/addcity", json={"stateName": state or "MockState", "cityName": city or "MockCity"}, timeout=5)
    except Exception:
        pass

def get_admin_token(base_url, admin_email="admin@example.com", admin_pass="Password123_"):
    """Logs in as admin to obtain JWT token required for bloodbank registration."""
    try:
        res = requests.post(f"{base_url}/api/admin/login", json={"email": admin_email, "password": admin_pass}, timeout=5)
        if res.status_code == 200:
            return res.json().get("token")
    except Exception:
        pass
    return None

def execute_system_registration(record, base_url="http://localhost:5000", simulate=False, cached_admin_token=None):
    """
    Executes registration for Admin, User, or Bloodbank.
    Returns (success: bool, remarks: str, new_admin_token: str)
    """
    role = str(record.get("role") or "").strip().lower()
    email = str(record.get("email") or "").strip()
    phone1 = str(record.get("phone1") or "").strip()
    password = str(record.get("password") or "Password123_")
    
    if not email:
        return False, "Missing Email in record", cached_admin_token
        
    if simulate:
        return True, f"{role.capitalize()} registered successfully (Simulated mode)", cached_admin_token

    # 1. ADMIN REGISTRATION
    if role == "admin":
        payload = {
            "email": email,
            "phoneNo": phone1 or "1234567890",
            "password": password,
            "passwordConfirm": password
        }
        try:
            res = requests.post(f"{base_url}/api/admin/register", json=payload, timeout=8)
            if res.status_code in [200, 201]:
                # Automatically login as this newly registered admin to get a fresh token
                token = get_admin_token(base_url, email, password)
                return True, "Admin registered successfully via API", token
            elif res.status_code in [400, 409, 500] and ("already exists" in res.text or "duplicate" in res.text or "Duplicate" in res.text):
                token = get_admin_token(base_url, email, password)
                return True, "Admin already exists (Verified)", token
            else:
                return False, f"Admin reg failed: HTTP {res.status_code} - {res.text[:60]}", cached_admin_token
        except Exception as e:
            return False, f"Admin reg error: {str(e)[:60]}", cached_admin_token

    # 2. USER / DONOR REGISTRATION
    elif role in ["user", "donor"]:
        state = str(record.get("state") or "MockState").strip()
        city = str(record.get("city") or "MockCity").strip()
        ensure_state_and_city(state, city, base_url)
        
        payload = {
            "firstName": str(record.get("name") or "User").strip(),
            "lastName": str(record.get("lastname_or_contact") or "Donor").strip(),
            "gender": str(record.get("gender") or "Male").strip(),
            "dob": str(record.get("dob_or_openingdate") or "1995-01-01").strip(),
            "age": int(record.get("age") or 30),
            "phoneNo1": phone1 or "9999999991",
            "phoneNo2": str(record.get("phone2") or phone1 or "9999999992").strip(),
            "email": email,
            "state": state,
            "city": city,
            "address": str(record.get("address1") or "123 Main St").strip(),
            "pinCode": int(record.get("pincode") or 123456),
            "password": password,
            "passwordConfirm": password
        }
        try:
            res = requests.post(f"{base_url}/api/user/register", json=payload, timeout=8)
            if res.status_code in [200, 201]:
                return True, "User registered successfully via API", cached_admin_token
            elif res.status_code in [400, 409, 500] and ("already exists" in res.text or "duplicate" in res.text):
                return True, "User already registered (Verified)", cached_admin_token
            else:
                return False, f"User reg failed: HTTP {res.status_code} - {res.text[:60]}", cached_admin_token
        except Exception as e:
            return False, f"User reg error: {str(e)[:60]}", cached_admin_token

    # 3. BLOODBANK REGISTRATION
    elif role in ["bloodbank", "hospital"]:
        state = str(record.get("state") or "MockState").strip()
        city = str(record.get("city") or "MockCity").strip()
        ensure_state_and_city(state, city, base_url)
        
        # We need an admin token to register bloodbank
        token = cached_admin_token or get_admin_token(base_url)
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
        payload = {
            "state": state,
            "city": city,
            "category": str(record.get("category") or "Government").strip(),
            "bloodbankName": str(record.get("name") or "Blood Bank").strip(),
            "contactPerson": str(record.get("lastname_or_contact") or "Dr. Incharge").strip(),
            "address1": str(record.get("address1") or "456 Hospital Rd").strip(),
            "address2": str(record.get("address2") or "Suite A").strip(),
            "pinCode": int(record.get("pincode") or 654321),
            "phoneNo1": phone1 or "8888888881",
            "phoneNo2": str(record.get("phone2") or phone1 or "8888888882").strip(),
            "email": email,
            "openingDate": str(record.get("dob_or_openingdate") or "2023-01-01").strip(),
            "password": password,
            "passwordConfirm": password
        }
        try:
            res = requests.post(f"{base_url}/api/bloodbank/register", json=payload, headers=headers, timeout=8)
            if res.status_code in [200, 201]:
                return True, "Bloodbank registered successfully via API", token
            elif res.status_code in [400, 409, 500] and ("already exists" in res.text or "duplicate" in res.text):
                return True, "Bloodbank already registered (Verified)", token
            else:
                return False, f"Bloodbank reg failed: HTTP {res.status_code} - {res.text[:60]}", token
        except Exception as e:
            return False, f"Bloodbank reg error: {str(e)[:60]}", token
            
    else:
        return False, f"Unknown role: {role}", cached_admin_token

def send_google_sheet_webhook_update(sheet_name="Registrations", row=None, email=None, status="Completed", remarks=""):
    """
    Sends live write-back request to the online Google Sheet Webhook.
    Instantly updates the cell inside Google Sheets in real-time!
    """
    load_env_config()
    webhook_url = os.getenv("GOOGLE_REGISTRATION_WEBHOOK_URL", "").strip() or os.getenv("GOOGLE_SHEET_WEBHOOK_URL", "").strip()
    if not webhook_url:
        print("        [Google Sheets Notice] Live webhook URL not set in automation/.env. Skipping online sheet write-back.")
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
            print(f"        [Google Sheet LIVE] Cell in online Google Sheet updated: Row {row} -> '{status}' (HTTP 200)")
            return True
        else:
            res_get = requests.get(webhook_url, params=payload, allow_redirects=True, timeout=12)
            if res_get.status_code == 200:
                print(f"        [Google Sheet LIVE] Cell in online Google Sheet updated via GET: Row {row} -> '{status}' (HTTP 200)")
                return True
            print(f"        [Google Sheet Warning] Webhook responded with HTTP {res.status_code}")
            return False
    except Exception as e:
        print(f"        [Google Sheet Live Notice] Webhook connection: {e}")
        return False

def sync_other_registration_file(other_path, row_idx, status="Completed", remarks=""):
    """Ensures both synced and local registration files stay in sync."""
    if not os.path.exists(other_path):
        return
    try:
        other_wb = openpyxl.load_workbook(other_path)
        other_ws = other_wb["Registrations"] if "Registrations" in other_wb.sheetnames else other_wb.active
        if 1 <= row_idx <= other_ws.max_row:
            fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
            font = Font(name="Calibri", size=11, bold=True, color="2E7D32")
            cell = other_ws.cell(row=row_idx, column=18, value=status)
            cell.fill = fill
            cell.font = font
            other_ws.cell(row=row_idx, column=19, value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            other_ws.cell(row=row_idx, column=20, value=remarks)
            other_wb.save(other_path)
        other_wb.close()
    except Exception:
        pass

def process_system_registration_queue(file_path=None, base_url="http://localhost:5000", simulate=False):
    """
    Main processor for Excel/Google Sheet system registrations:
    1. Loads Excel file (synced Google Sheet or local queue).
    2. Filters rows where Status is 'Pending' or null/empty.
    3. Skips already 'Completed' rows.
    4. Registers Admin, User, or Bloodbank.
    5. Upon completion, marks Status as 'Completed', records Completed Date and Remarks.
    6. Saves the updated Excel workbook.
    """
    if file_path is None:
        file_path = get_active_registration_file()
        
    if not os.path.exists(file_path):
        create_or_reset_registration_excel(file_path)
        
    wb = openpyxl.load_workbook(file_path)
    # Check for Registrations sheet or first active sheet
    ws = wb["Registrations"] if "Registrations" in wb.sheetnames else wb.active
    
    # Map headers to 1-based column indices
    header_map = {}
    for col_idx in range(1, ws.max_column + 1):
        val = ws.cell(row=1, column=col_idx).value
        if val:
            header_map[str(val).strip().lower()] = col_idx
            
    status_col = header_map.get("status", 18)
    date_col = header_map.get("completed date", 19)
    remarks_col = header_map.get("remarks", 20)
    role_col = header_map.get("role", 2)
    email_col = header_map.get("email", 5)
    name_col = header_map.get("name", 3)
    
    completed_fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
    completed_font = Font(name="Calibri", size=11, bold=True, color="2E7D32")
    
    total_rows = ws.max_row - 1
    processed_count = 0
    skipped_count = 0
    failed_count = 0
    
    print("\n" + "=" * 65)
    print(f"PROCESSING SYSTEM REGISTRATIONS FROM EXCEL: {os.path.basename(file_path)}")
    print(f"Total Registration Records: {total_rows}")
    print("=" * 65)
    
    admin_token = None
    
    for row_idx in range(2, ws.max_row + 1):
        status_val = ws.cell(row=row_idx, column=status_col).value
        role_val = ws.cell(row=row_idx, column=role_col).value or "User"
        email_val = ws.cell(row=row_idx, column=email_col).value or ""
        name_val = ws.cell(row=row_idx, column=name_col).value or ""
        
        # Build dictionary of row data
        row_dict = {}
        for h_name, c_idx in header_map.items():
            row_dict[h_name] = ws.cell(row=row_idx, column=c_idx).value
            
        # Only process if status is Pending or null/empty
        if is_pending_or_null(status_val):
            print(f"\n[Row {row_idx}] Match Found -> Status is '{status_val}' (Pending/Null)")
            print(f"        Role: {role_val} | Name: {name_val} | Email: {email_val}")
            
            success, remarks, admin_token = execute_system_registration(
                record=row_dict,
                base_url=base_url,
                simulate=simulate,
                cached_admin_token=admin_token
            )
            
            if success:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status_cell = ws.cell(row=row_idx, column=status_col, value="Completed")
                status_cell.fill = completed_fill
                status_cell.font = completed_font
                
                ws.cell(row=row_idx, column=date_col, value=now_str)
                ws.cell(row=row_idx, column=remarks_col, value=remarks)
                
                processed_count += 1
                print(f"        -> STATUS UPDATED TO 'Completed' at {now_str}")
                print(f"        -> Remarks: {remarks}")
                
                # Send live update to online Google Sheet directly
                send_google_sheet_webhook_update(
                    sheet_name="Registrations",
                    row=row_idx,
                    email=email_val,
                    status="Completed",
                    remarks=remarks
                )
                
                # Sync other local file
                other_file = DEFAULT_REG_EXCEL_PATH if os.path.abspath(file_path) != os.path.abspath(DEFAULT_REG_EXCEL_PATH) else SYNCED_REG_EXCEL_PATH
                sync_other_registration_file(other_file, row_idx, "Completed", remarks)
            else:
                failed_count += 1
                ws.cell(row=row_idx, column=remarks_col, value=remarks)
                print(f"        -> FAILED: {remarks}")
        else:
            skipped_count += 1
            print(f"[Row {row_idx}] SKIPPED -> {role_val}: {email_val} (Status is '{status_val}')")
            
    wb.save(file_path)
    wb.close()
    
    print("\n" + "=" * 65)
    print("SYSTEM REGISTRATION AUTOMATION SUMMARY:")
    print(f"  - Registrations Processed & Completed: {processed_count}")
    print(f"  - Rows Skipped (Already Completed):   {skipped_count}")
    print(f"  - Rows Failed:                        {failed_count}")
    print(f"  - Updated File Saved at: {file_path}")
    print("=" * 65 + "\n")
    
    return {
        "total": total_rows,
        "processed": processed_count,
        "skipped": skipped_count,
        "failed": failed_count,
        "file_path": file_path
    }

if __name__ == "__main__":
    simulate_mode = "--simulate" in sys.argv or os.getenv("RPA_SIMULATE", "false").lower() == "true"
    
    if "--reset" in sys.argv:
        create_or_reset_registration_excel()
        sys.exit(0)
    else:
        stats = process_system_registration_queue(simulate=simulate_mode)

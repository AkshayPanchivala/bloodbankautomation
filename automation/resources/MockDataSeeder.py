import os
import sys
import requests
import openpyxl
from datetime import datetime, timedelta, timezone

# Ensure resources folder is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ExcelHelper import (
    load_env_config, 
    is_pending_or_null, 
    get_active_excel_file, 
    DEFAULT_EXCEL_PATH
)
from SystemRegistrationRpa import (
    get_active_registration_file, 
    DEFAULT_REG_EXCEL_PATH, 
    create_or_reset_registration_excel
)
from ExcelDataDriver import ExcelDataDriver

BASE_URL = "http://localhost:5000/api"

def seed_states_and_cities_from_excel(records):
    """Dynamically seeds state and city combinations found in pending/blank Excel rows."""
    seen = set()
    for rec in records:
        # Only check states/cities from pending/blank rows
        if is_pending_or_null(rec.get("status")):
            state = str(rec.get("state") or "").strip()
            city = str(rec.get("city") or "").strip()
            if state and (state, "") not in seen:
                try:
                    requests.post(f"{BASE_URL}/state", json={"stateName": state}, timeout=5)
                    seen.add((state, ""))
                except Exception:
                    pass
            if state and city and (state, city) not in seen:
                try:
                    requests.post(f"{BASE_URL}/city/addcity", json={"stateName": state, "cityName": city}, timeout=5)
                    seen.add((state, city))
                except Exception:
                    pass
                    
    # Always ensure default MockState and MockCity exist for baseline test compatibility
    try:
        requests.post(f"{BASE_URL}/state", json={"stateName": "MockState"}, timeout=5)
        requests.post(f"{BASE_URL}/city/addcity", json={"stateName": "MockState", "cityName": "MockCity"}, timeout=5)
    except Exception:
        pass

def read_records_from_workbook(file_path, sheet_name=None):
    """Reads all rows from an Excel file into a list of dicts."""
    if not os.path.exists(file_path):
        return []
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active
        
        header_map = {}
        for col_idx in range(1, ws.max_column + 1):
            val = ws.cell(row=1, column=col_idx).value
            if val:
                header_map[str(val).strip().lower()] = col_idx
                
        records = []
        for row_idx in range(2, ws.max_row + 1):
            rec = {}
            for h_name, c_idx in header_map.items():
                val = ws.cell(row=row_idx, column=c_idx).value
                rec[h_name] = "" if val is None else str(val).strip()
            rec["_row_idx"] = row_idx
            records.append(rec)
        wb.close()
        return records
    except Exception as e:
        print(f"[Seeder] Error reading {file_path}: {e}")
        return []

def seed_mock_data():
    """
    Main Data Seeder:
    ONLY seeds records where Status is 'Pending' or blank/null.
    Completed records are skipped.
    Upon successful feed into the system, updates Status to 'Completed' in the Excel sheet.
    """
    print("\n" + "=" * 65)
    print("SEEDING DATABASE: ONLY PENDING OR BLANK ROWS FROM EXCEL")
    print("=" * 65)
    
    data_driver = ExcelDataDriver()
    
    # 1. Get active Master Registration Excel file (synced from Google Sheet if URL set)
    reg_file = get_active_registration_file()
    print(f"[Seeder] Checking registration records in: {reg_file}")
    
    reg_records = read_records_from_workbook(reg_file, "Registrations")
    print(f"[Seeder] Total records in sheet: {len(reg_records)}")
    
    # Dynamically seed States and Cities from pending rows
    seed_states_and_cities_from_excel(reg_records)
    
    # Ensure baseline admin token is available for bloodbank creation
    default_admin_token = None
    try:
        requests.post(f"{BASE_URL}/admin/register", json={
            "phoneNo": "1234567890", "email": "admin@example.com", 
            "password": "Password123_", "passwordConfirm": "Password123_"
        }, timeout=5)
        l_res = requests.post(f"{BASE_URL}/admin/login", json={"email": "admin@example.com", "password": "Password123_"}, timeout=5)
        if l_res.status_code == 200:
            default_admin_token = l_res.json().get("token")
    except Exception:
        pass

    # Ensure baseline user and bloodbank exist for login tests
    try:
        requests.post(f"{BASE_URL}/user/register", json={
            "firstName": "Mock", "lastName": "User", "gender": "Male", "dob": "1990-01-01", "age": 34,
            "phoneNo1": "9999999991", "phoneNo2": "9999999992", "email": "mockuser@example.com",
            "state": "MockState", "city": "MockCity", "address": "123 Mock St", "pinCode": 123456,
            "password": "Password123_", "passwordConfirm": "Password123_"
        }, timeout=5)
    except Exception:
        pass

    if default_admin_token:
        try:
            requests.post(f"{BASE_URL}/bloodbank/register", json={
                "state": "MockState", "city": "MockCity", "category": "Government",
                "bloodbankName": "Mock Bloodbank", "contactPerson": "Dr. Mock",
                "address1": "456 Blood Ave", "address2": "Suite B", "pinCode": 654321,
                "phoneNo1": "8888888881", "phoneNo2": "8888888882", "email": "mockbloodbank@example.com",
                "openingDate": "2023-01-01", "password": "Password123_", "passwordConfirm": "Password123_"
            }, headers={"Authorization": f"Bearer {default_admin_token}"}, timeout=5)
        except Exception:
            pass

    admin_seeded = 0
    user_seeded = 0
    bb_seeded = 0
    skipped_count = 0

    # 2. Process Registration Rows (ONLY Pending or Blank)
    for rec in reg_records:
        row_idx = rec["_row_idx"]
        status_val = rec.get("status")
        role = rec.get("role", "").lower()
        email = rec.get("email")

        # FILTER: ONLY PENDING OR BLANK STATUS
        if not is_pending_or_null(status_val):
            skipped_count += 1
            print(f"  [Row {row_idx}] SKIPPED -> {rec.get('role')}: {email} (Status is '{status_val}')")
            continue

        print(f"  [Row {row_idx}] PROCESSING (Pending/Blank) -> Role: {rec.get('role')} | Email: {email}")

        # A. ADMIN SEED
        if role == "admin" and email:
            phone = rec.get("phone1") or "1234567890"
            password = rec.get("password") or "Password123_"
            admin_payload = {
                "phoneNo": str(phone),
                "email": email,
                "password": password,
                "passwordConfirm": password
            }
            try:
                res = requests.post(f"{BASE_URL}/admin/register", json=admin_payload, timeout=5)
                success = res.status_code in [200, 201] or "already exists" in res.text.lower()
                if success:
                    data_driver.mark_registration_record_completed(
                        row_index=row_idx, 
                        file_path=reg_file, 
                        remarks="Admin seeded into database successfully"
                    )
                    admin_seeded += 1
                    print(f"    -> Admin Seeded & Marked Completed in Excel!")
                else:
                    print(f"    -> Admin Seed Failed: HTTP {res.status_code} - {res.text[:50]}")
            except Exception as e:
                print(f"    -> Admin Seed Error: {e}")

        # B. USER SEED
        elif role in ["user", "donor"] and email:
            first_name = rec.get("name") or "User"
            last_name = rec.get("lastname_or_contact") or "Donor"
            state = rec.get("state") or "MockState"
            city = rec.get("city") or "MockCity"
            phone1 = rec.get("phone1") or "9999999991"
            phone2 = rec.get("phone2") or phone1
            password = rec.get("password") or "Password123_"
            
            p1_digits = ''.join(filter(str.isdigit, str(phone1))) or "9999999991"
            p2_digits = ''.join(filter(str.isdigit, str(phone2))) or p1_digits
            
            try:
                age_val = int(float(rec.get("age") or 30))
            except Exception:
                age_val = 30

            user_payload = {
                "firstName": first_name,
                "lastName": last_name,
                "gender": rec.get("gender") or "Male",
                "dob": rec.get("dob_or_openingdate") or "1995-01-01",
                "age": age_val,
                "phoneNo1": p1_digits,
                "phoneNo2": p2_digits,
                "email": email,
                "state": state,
                "city": city,
                "address": rec.get("address1") or "123 Main St",
                "pinCode": int(float(rec.get("pincode") or 123456)),
                "password": password,
                "passwordConfirm": password
            }
            try:
                res = requests.post(f"{BASE_URL}/user/register", json=user_payload, timeout=5)
                success = res.status_code in [200, 201] or "already exists" in res.text.lower()
                if success:
                    data_driver.mark_registration_record_completed(
                        row_index=row_idx, 
                        file_path=reg_file, 
                        remarks="User seeded into database successfully"
                    )
                    user_seeded += 1
                    print(f"    -> User Seeded & Marked Completed in Excel!")
                else:
                    print(f"    -> User Seed Failed: HTTP {res.status_code} - {res.text[:50]}")
            except Exception as e:
                print(f"    -> User Seed Error: {e}")

        # C. BLOODBANK SEED
        elif role in ["bloodbank", "hospital"] and email:
            bb_name = rec.get("name") or "Blood Bank"
            contact = rec.get("lastname_or_contact") or "Dr. Incharge"
            state = rec.get("state") or "MockState"
            city = rec.get("city") or "MockCity"
            category = rec.get("category") or "Government"
            if category not in ["Government", "RedCross", "Private"]:
                category = "Government"
                
            phone1 = rec.get("phone1") or "8888888881"
            phone2 = rec.get("phone2") or phone1
            password = rec.get("password") or "Password123_"
            
            bb_payload = {
                "state": state,
                "city": city,
                "category": category,
                "bloodbankName": bb_name,
                "contactPerson": contact,
                "address1": rec.get("address1") or "456 Hospital Rd",
                "address2": rec.get("address2") or "Suite A",
                "pinCode": int(float(rec.get("pincode") or 654321)),
                "phoneNo1": str(phone1),
                "phoneNo2": str(phone2),
                "email": email,
                "openingDate": rec.get("dob_or_openingdate") or "2023-01-01",
                "password": password,
                "passwordConfirm": password
            }
            headers = {"Authorization": f"Bearer {default_admin_token}"} if default_admin_token else {}
            try:
                res = requests.post(f"{BASE_URL}/bloodbank/register", json=bb_payload, headers=headers, timeout=5)
                success = res.status_code in [200, 201] or "already exists" in res.text.lower()
                if success:
                    data_driver.mark_registration_record_completed(
                        row_index=row_idx, 
                        file_path=reg_file, 
                        remarks="Bloodbank seeded into database successfully"
                    )
                    bb_seeded += 1
                    print(f"    -> Bloodbank Seeded & Marked Completed in Excel!")
                else:
                    print(f"    -> Bloodbank Seed Failed: HTTP {res.status_code} - {res.text[:50]}")
            except Exception as e:
                print(f"    -> Bloodbank Seed Error: {e}")

    # 3. Process Donor Motivation Rows (ONLY Pending or Blank)
    donor_file = get_active_excel_file()
    donor_records = read_records_from_workbook(donor_file, "DonorQueue")
    donor_seeded = 0
    
    for d_rec in donor_records:
        d_idx = d_rec["_row_idx"]
        d_status = d_rec.get("status")
        d_email = d_rec.get("email")
        
        # FILTER: ONLY PENDING OR BLANK STATUS
        if not is_pending_or_null(d_status):
            continue
            
        print(f"  [Donor Row {d_idx}] PROCESSING (Pending/Blank) -> Email: {d_email}")
        
        # In mock/seeder mode, mark donor row as processed
        data_driver.mark_donor_record_completed(
            row_index=d_idx,
            file_path=donor_file,
            remarks="Donor verified and seeded in system"
        )
        donor_seeded += 1

    print("\n" + "=" * 65)
    print("DATA SEEDING COMPLETE!")
    print(f"  - Pending/Blank Admins Seeded:      {admin_seeded}")
    print(f"  - Pending/Blank Users Seeded:       {user_seeded}")
    print(f"  - Pending/Blank Bloodbanks Seeded:  {bb_seeded}")
    print(f"  - Pending/Blank Donors Processed:   {donor_seeded}")
    print(f"  - Rows Skipped (Already Completed): {skipped_count}")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    seed_mock_data()

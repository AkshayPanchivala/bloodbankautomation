import os
import sys
import openpyxl
from openpyxl.styles import Font, PatternFill
from datetime import datetime
import requests

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

class ExcelDataDriver:
    """
    Robot Framework keyword library for reading test data from Excel / Google Sheet
    and writing execution results back to the sheet.
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def get_pending_registration_record(self, role="User", file_path=None):
        """
        Finds and returns the first row from the registration Excel/Google Sheet
        where Role matches and Status is 'Pending' or null/empty.
        Returns a dict of the row data, or None if no pending row found.
        """
        if file_path is None:
            file_path = get_active_registration_file()
            
        if not os.path.exists(file_path):
            create_or_reset_registration_excel(file_path)

        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb["Registrations"] if "Registrations" in wb.sheetnames else wb.active

        # Map header name to column index (1-based)
        header_map = {}
        for col_idx in range(1, ws.max_column + 1):
            val = ws.cell(row=1, column=col_idx).value
            if val:
                header_map[str(val).strip().lower()] = col_idx

        status_col = header_map.get("status", 18)
        role_col = header_map.get("role", 2)

        target_role = str(role).strip().lower() if role else None

        for row_idx in range(2, ws.max_row + 1):
            row_role = str(ws.cell(row=row_idx, column=role_col).value or "").strip().lower()
            row_status = ws.cell(row=row_idx, column=status_col).value

            # Check if role matches and status is Pending or null
            if (target_role is None or row_role == target_role) and is_pending_or_null(row_status):
                record = {}
                for h_name, c_idx in header_map.items():
                    val = ws.cell(row=row_idx, column=c_idx).value
                    record[h_name] = "" if val is None else str(val)
                
                record["_row_idx"] = row_idx
                record["_file_path"] = file_path
                wb.close()
                print(f"[ExcelDataDriver] Found pending {role} record at row {row_idx}: {record.get('email')}")
                return record

        wb.close()
        print(f"[ExcelDataDriver] No pending {role} records found in {file_path}")
        return None

    def _update_workbook_row_status(self, target_path, row_idx=None, email=None, status="Completed", remarks=""):
        """Helper to mark Status column as Completed in a given workbook file."""
        if not os.path.exists(target_path):
            return False
            
        try:
            wb = openpyxl.load_workbook(target_path)
            ws = wb["Registrations"] if "Registrations" in wb.sheetnames else wb.active

            header_map = {}
            for col_idx in range(1, ws.max_column + 1):
                val = ws.cell(row=1, column=col_idx).value
                if val:
                    header_map[str(val).strip().lower()] = col_idx

            status_col = header_map.get("status", 18)
            date_col = header_map.get("completed date", 19)
            remarks_col = header_map.get("remarks", 20)
            email_col = header_map.get("email", 5)

            completed_fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
            completed_font = Font(name="Calibri", size=11, bold=True, color="2E7D32")
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            matched_row = None
            if row_idx and 1 <= int(row_idx) <= ws.max_row:
                matched_row = int(row_idx)
            elif email:
                for r in range(2, ws.max_row + 1):
                    if str(ws.cell(row=r, column=email_col).value or "").strip().lower() == email.strip().lower():
                        matched_row = r
                        break

            if matched_row:
                status_cell = ws.cell(row=matched_row, column=status_col, value=status)
                status_cell.fill = completed_fill
                status_cell.font = completed_font
                ws.cell(row=matched_row, column=date_col, value=now_str)
                ws.cell(row=matched_row, column=remarks_col, value=remarks)
                wb.save(target_path)
                wb.close()
                print(f"[ExcelDataDriver] Marked row {matched_row} as '{status}' in {os.path.basename(target_path)}")
                return True
            wb.close()
            return False
        except Exception as e:
            print(f"[ExcelDataDriver] Warning updating {target_path}: {e}")
            return False

    def mark_registration_record_completed(self, row_index, file_path=None, remarks="UI form submitted successfully", email=None):
        """
        Updates the Status of the given row in the Excel sheet to 'Completed',
        records the Completed Date timestamp, and writes remarks.
        Updates BOTH local Excel files and sends webhook to update the live online Google Sheet!
        """
        row_idx = int(row_index)
        if file_path is None:
            file_path = get_active_registration_file()

        # Update primary file (e.g. google_registration_synced.xlsx)
        self._update_workbook_row_status(
            target_path=file_path, 
            row_idx=row_idx, 
            status="Completed", 
            remarks=remarks
        )

        # Update local file (system_registration_queue.xlsx)
        if os.path.abspath(file_path) != os.path.abspath(DEFAULT_REG_EXCEL_PATH) and os.path.exists(DEFAULT_REG_EXCEL_PATH):
            self._update_workbook_row_status(
                target_path=DEFAULT_REG_EXCEL_PATH, 
                row_idx=row_idx, 
                status="Completed", 
                remarks=remarks
            )

        # Online Google Sheet live write-back webhook
        load_env_config()
        webhook_url = os.getenv("GOOGLE_REGISTRATION_WEBHOOK_URL", "").strip() or os.getenv("GOOGLE_SHEET_WEBHOOK_URL", "").strip()
        if webhook_url:
            try:
                payload = {
                    "sheet": "Registrations",
                    "row": row_idx,
                    "email": email,
                    "status": "Completed",
                    "completedDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "remarks": remarks
                }
                res = requests.post(webhook_url, json=payload, allow_redirects=True, timeout=12)
                if res.status_code == 200:
                    print(f"[ExcelDataDriver] Online Google Sheet updated successfully via Webhook: HTTP {res.status_code}")
                else:
                    res_get = requests.get(webhook_url, params=payload, allow_redirects=True, timeout=12)
                    if res_get.status_code == 200:
                        print(f"[ExcelDataDriver] Online Google Sheet updated via GET Webhook: HTTP {res_get.status_code}")
                    else:
                        print(f"[ExcelDataDriver] Webhook response: HTTP {res.status_code}")
            except Exception as e:
                print(f"[ExcelDataDriver] Webhook notice: {e}")

        return True

    def get_pending_donor_record(self, file_path=None):
        """
        Finds and returns the first row from the donor queue Excel/Google Sheet
        where Status is 'Pending' or null/empty.
        """
        if file_path is None:
            file_path = get_active_excel_file()

        if not os.path.exists(file_path):
            return None

        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb["DonorQueue"] if "DonorQueue" in wb.sheetnames else wb.active

        header_map = {}
        for col_idx in range(1, ws.max_column + 1):
            val = ws.cell(row=1, column=col_idx).value
            if val:
                header_map[str(val).strip().lower()] = col_idx

        status_col = header_map.get("status", 6)

        for row_idx in range(2, ws.max_row + 1):
            row_status = ws.cell(row=row_idx, column=status_col).value
            if is_pending_or_null(row_status):
                record = {}
                for h_name, c_idx in header_map.items():
                    val = ws.cell(row=row_idx, column=c_idx).value
                    record[h_name] = "" if val is None else str(val)

                record["_row_idx"] = row_idx
                record["_file_path"] = file_path
                wb.close()
                return record

        wb.close()
        return None

    def mark_donor_record_completed(self, row_index, file_path=None, remarks="Processed successfully", email=None):
        """
        Updates the Status of the given donor row in the Excel sheet to 'Completed'.
        Updates local file and sends webhook to update the live online Google Sheet!
        """
        row_idx = int(row_index)
        if file_path is None:
            file_path = get_active_excel_file()

        def update_donor_file(f_path):
            if not os.path.exists(f_path):
                return False
            try:
                wb = openpyxl.load_workbook(f_path)
                ws = wb["DonorQueue"] if "DonorQueue" in wb.sheetnames else wb.active

                header_map = {}
                for col_idx in range(1, ws.max_column + 1):
                    val = ws.cell(row=1, column=col_idx).value
                    if val:
                        header_map[str(val).strip().lower()] = col_idx

                status_col = header_map.get("status", 6)
                date_col = header_map.get("completed date", 7)
                remarks_col = header_map.get("remarks", 8)

                completed_fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
                completed_font = Font(name="Calibri", size=11, bold=True, color="2E7D32")
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                status_cell = ws.cell(row=row_idx, column=status_col, value="Completed")
                status_cell.fill = completed_fill
                status_cell.font = completed_font
                ws.cell(row=row_idx, column=date_col, value=now_str)
                ws.cell(row=row_idx, column=remarks_col, value=remarks)

                wb.save(f_path)
                wb.close()
                print(f"[ExcelDataDriver] Marked donor row {row_idx} as 'Completed' in {os.path.basename(f_path)}")
                return True
            except Exception as e:
                print(f"[ExcelDataDriver] Warning updating donor file {f_path}: {e}")
                return False

        update_donor_file(file_path)
        if os.path.abspath(file_path) != os.path.abspath(DEFAULT_EXCEL_PATH) and os.path.exists(DEFAULT_EXCEL_PATH):
            update_donor_file(DEFAULT_EXCEL_PATH)

        # Online Google Sheet live write-back webhook for donor
        load_env_config()
        webhook_url = os.getenv("GOOGLE_DONOR_WEBHOOK_URL", "").strip() or os.getenv("GOOGLE_SHEET_WEBHOOK_URL", "").strip()
        if webhook_url:
            try:
                payload = {
                    "sheet": "DonorQueue",
                    "row": row_idx,
                    "email": email,
                    "status": "Completed",
                    "completedDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "remarks": remarks
                }
                res = requests.post(webhook_url, json=payload, allow_redirects=True, timeout=12)
                if res.status_code == 200:
                    print(f"[ExcelDataDriver] Online Google Sheet updated successfully via Webhook: HTTP {res.status_code}")
                else:
                    res_get = requests.get(webhook_url, params=payload, allow_redirects=True, timeout=12)
                    if res_get.status_code == 200:
                        print(f"[ExcelDataDriver] Online Google Sheet updated via GET Webhook: HTTP {res_get.status_code}")
                    else:
                        print(f"[ExcelDataDriver] Webhook response: HTTP {res.status_code}")
            except Exception as e:
                print(f"[ExcelDataDriver] Webhook notice: {e}")

        return True

if __name__ == "__main__":
    driver = ExcelDataDriver()
    rec = driver.get_pending_registration_record("User")
    print("Pending User:", rec)

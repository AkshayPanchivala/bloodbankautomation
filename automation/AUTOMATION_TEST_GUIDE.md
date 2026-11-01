# Blood Bank Automation Suite — Complete Test & Google Sheets Guide

This guide documents every command to run tests individually or together, how the Excel/Google Sheet data-driven automation works, and how to mark cells as **`Completed`** directly inside your online Google Spreadsheet in real time.

---

## 1. Why Online Google Sheets Need a Webhook to Update

* When tests download data from a Google Sheet URL, Google provides an **Export Copy** (`.xlsx`) via HTTP GET.
* Editing this file on your computer modifies the **local file**, but **Google does not allow any external computer to write into your Google Drive without authorization**.
* By deploying a **1-minute Google Apps Script Webhook** (provided in [`automation/google_sheets_apps_script.js`](file:///f:/Projects/blood_bank_management/automation/google_sheets_apps_script.js)), Google grants permission to update cells.
* Whenever a test finishes, it sends an instant notification to this Webhook, and **your Google Sheet in Google Chrome updates directly online in real time (Row 8 Status -> Completed with Green background)**!

---

## 2. 1-Minute Setup to Update Cells Directly Inside Google Sheets

### Step 1: Open Apps Script in Google Sheets
1. Open your Google Spreadsheet in Google Chrome:
   👉 **[RegistrationSheet](https://docs.google.com/spreadsheets/d/18ORNC2fzAbziNLsDUZ3u6VEh6_isZHOBNkuFg73t0a8/edit)**
2. In the top menu, click **Extensions** $\to$ **Apps Script**.

### Step 2: Paste the Webhook Code
1. Delete any existing text inside the Apps Script code editor.
2. Copy and paste the entire contents of [`automation/google_sheets_apps_script.js`](file:///f:/Projects/blood_bank_management/automation/google_sheets_apps_script.js) (or copy the snippet below):

```javascript
function doPost(e) {
  var data = {};
  if (e && e.postData && e.postData.contents) {
    try { data = JSON.parse(e.postData.contents); } catch (err) { data = e.parameter || {}; }
  } else if (e && e.parameter) {
    data = e.parameter;
  }
  return handleLiveUpdate(data);
}

function doGet(e) {
  var data = (e && e.parameter) ? e.parameter : {};
  if (data.row || data.email || data.status) return handleLiveUpdate(data);
  return ContentService.createTextOutput(JSON.stringify({
    status: "online",
    message: "Google Sheet Live Automation Webhook is READY & CONNECTED!"
  })).setMimeType(ContentService.MimeType.JSON);
}

function handleLiveUpdate(data) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = data.sheet ? ss.getSheetByName(data.sheet) : ss.getActiveSheet();
    if (!sheet) sheet = ss.getActiveSheet();
    
    var lastRow = sheet.getLastRow();
    var lastCol = sheet.getLastColumn();
    var headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
    
    var statusCol = -1, dateCol = -1, remarksCol = -1, emailCol = -1;
    for (var c = 0; c < headers.length; c++) {
      var h = String(headers[c] || "").trim().toLowerCase();
      if (h === "status") statusCol = c + 1;
      else if (h === "completed date" || h === "completed_date") dateCol = c + 1;
      else if (h === "remarks") remarksCol = c + 1;
      else if (h === "email") emailCol = c + 1;
    }
    if (statusCol === -1) statusCol = 18;
    if (dateCol === -1) dateCol = 19;
    if (remarksCol === -1) remarksCol = 20;
    
    var targetRow = data.row ? Number(data.row) : null;
    var targetEmail = data.email ? String(data.email).trim().toLowerCase() : null;
    
    if (!targetRow && targetEmail && emailCol !== -1 && lastRow >= 2) {
      var emailValues = sheet.getRange(2, emailCol, lastRow - 1, 1).getValues();
      for (var r = 0; r < emailValues.length; r++) {
        if (String(emailValues[r][0] || "").trim().toLowerCase() === targetEmail) {
          targetRow = r + 2;
          break;
        }
      }
    }
    
    if (!targetRow && lastRow >= 2) {
      var statusValues = sheet.getRange(2, statusCol, lastRow - 1, 1).getValues();
      for (var s = 0; s < statusValues.length; s++) {
        var sVal = String(statusValues[s][0] || "").trim().toLowerCase();
        if (sVal === "pending" || sVal === "" || sVal === "null" || sVal === "none") {
          targetRow = s + 2;
          break;
        }
      }
    }
    
    if (targetRow && targetRow <= lastRow) {
      var newStatus = data.status || "Completed";
      var statusCell = sheet.getRange(targetRow, statusCol);
      statusCell.setValue(newStatus);
      statusCell.setBackground("#E8F5E9");
      statusCell.setFontColor("#2E7D32");
      statusCell.setFontWeight("bold");
      
      var tz = Session.getScriptTimeZone() || "GMT+5:30";
      var nowStr = data.completedDate || Utilities.formatDate(new Date(), tz, "yyyy-MM-dd HH:mm:ss");
      sheet.getRange(targetRow, dateCol).setValue(nowStr);
      if (data.remarks) sheet.getRange(targetRow, remarksCol).setValue(data.remarks);
      SpreadsheetApp.flush();
      
      return ContentService.createTextOutput(JSON.stringify({
        status: "success", updatedRow: targetRow, newStatus: newStatus, completedDate: nowStr
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    return ContentService.createTextOutput(JSON.stringify({status: "error", message: "Target row not found"}))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({status: "error", message: err.toString()}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
```

### Step 3: Deploy as Web App
1. Click the blue **Deploy** button (top right) $\to$ **New deployment**.
2. Click the gear icon (⚙️) next to "Select type" $\to$ choose **Web app**.
3. Fill in:
   * **Description:** `Live Automation Webhook`
   * **Execute as:** `Me` (your Google account)
   * **Who has access:** `Anyone` *(Crucial: allows test runners to send updates)*
4. Click **Deploy**.
5. Click **Authorize access** $\to$ choose your account $\to$ click **Advanced** $\to$ click **Go to Untitled project (unsafe)** $\to$ click **Allow**.
6. Copy the **Web App URL** (e.g. `https://script.google.com/macros/s/AKfycbx.../exec`).

### Step 4: Paste URL into `automation/.env`
Open [`automation/.env`](file:///f:/Projects/blood_bank_management/automation/.env) and paste your URL:
```env
GOOGLE_REGISTRATION_WEBHOOK_URL=https://script.google.com/macros/s/AKfycbx.../exec
```

### Step 5: Test It Instantly!
Run this command from your terminal:
```cmd
cd f:\Projects\blood_bank_management\automation
test_google_sheet.bat
```
👀 **Look at your open Google Sheet tab in Google Chrome right now: Row 8 Column R (`Status`) immediately turns green and changes to `Completed`!**

---

## 3. Individual Test Execution Commands

Run any of the batch files below from `f:\Projects\blood_bank_management\automation`:

| Batch File | Target | Description | Live Google Sheet Effect |
| :--- | :--- | :--- | :--- |
| **`test_google_sheet.bat`** | Live Webhook Verification | Pings webhook and marks Row 8 as `Completed` directly in Chrome. | Updates Row 8 instantly |
| **`run_excel_registration.bat`** | Excel / Google Registrations | Reads next pending Admin, User, or Bloodbank from sheet, registers them, and marks `Completed`. | Updates pending row to `Completed` |
| **`run_ui_register.bat`** | User Registration UI | Opens browser, signs up next pending User from sheet, marks `Completed`. | Updates User row to `Completed` |
| **`run_ui_admin.bat`** | Admin Bloodbank UI | Logs in as Admin, adds bloodbank using next pending Bloodbank row, marks `Completed`. | Updates Bloodbank row to `Completed` |
| **`run_ui_login.bat`** | Login UI | Verifies login for registered users. | UI Test |
| **`run_ui_donate.bat`** | Donation UI | Verifies donor donation flow. | UI Test |
| **`run_ui_bloodbank.bat`** | Bloodbank Dashboard UI | Verifies bloodbank inventory display. | UI Test |
| **`run_excel.bat donor`** | Donor Motivation RPA | Scans eligible donors from `DonorQueue` sheet, sends alerts, marks `Completed`. | Updates `DonorQueue` sheet |
| **`run_excel.bat all`** | All Excel Automations | Runs both Master Registrations and Donor Motivation automations. | Updates both sheets |
| **`run_ui.bat all`** | Full UI Suite | Runs all UI browser tests sequentially. | Updates UI test rows |
| **`run_api.bat`** | Backend API Tests | Verifies `/api/bloodbank/getbloodbanks` and core API endpoints. | API Test |
| **`run_rpa.bat`** | Full RPA Tasks | Runs email motivation and stock alert RPA scripts. | RPA Alert |
| **`run_all.bat`** | Full Complete Suite | Runs API tests + UI tests + RPA tasks. | Runs everything |
| **`reset_excel_data.bat`** | Reset Local Queues | Resets local Excel files with fresh pending rows. | Local Reset |

---

## 4. How the Data Filtering Works

1. **Only Pending / Blank Status Rows are Processed:**
   * The automation strictly filters rows where **`Status`** is `"Pending"` (case-insensitive) or `null` / empty (`""`, `"none"`, `"nan"`).
   * Any row already marked **`Completed`** is skipped automatically.
2. **Real-time Live Online Update:**
   * Once a record is processed, the bot sends an instant update:
     * **`Status`** $\to$ **`Completed`** (Green cell `#E8F5E9`)
     * **`Completed Date`** $\to$ Current timestamp (e.g. `2026-11-01 10:15:30`)
     * **`Remarks`** $\to$ Execution summary (e.g. `Admin registered successfully`)
   * Changes immediately appear inside your **Google Sheet in Chrome** and in the local `.xlsx` files!

---

## 5. Visual HTML Reports & Logs

After running any test, view the visual execution report:
* **HTML Report:** [`automation\results\report.html`](file:///f:/Projects/blood_bank_management/automation/results/report.html)
* **Detailed Execution Log:** [`automation\results\log.html`](file:///f:/Projects/blood_bank_management/automation/results/log.html)

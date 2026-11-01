# Google Sheets Live Webhook Setup Guide

This guide provides step-by-step instructions to configure **live, two-way synchronization** between your automation test suite and your Google Spreadsheets. 

When configured, every time a test finishes, it will **directly update the cell in your online Google Sheet in Google Chrome** from `Pending` $\to$ `Completed` (highlighted in green) in real-time.

---

## 1. Overview of Webhooks Needed

Your `automation/.env` file requires two webhook URLs:

| Environment Variable | Target Spreadsheet | Sheet Tab | Purpose |
| :--- | :--- | :--- | :--- |
| **`GOOGLE_REGISTRATION_WEBHOOK_URL`** | [RegistrationSheet](https://docs.google.com/spreadsheets/d/18ORNC2fzAbziNLsDUZ3u6VEh6_isZHOBNkuFg73t0a8/edit) | `Registrations` | Admin, User & Bloodbank registrations |
| **`GOOGLE_DONOR_WEBHOOK_URL`** | [DonorQueue Sheet](https://docs.google.com/spreadsheets/d/1Z5OXbxG0ZWzlIxiyuMj4mTNB7mDsFGwBcEi1WnL5Nbw/edit) | `DonorQueue` | Donor motivation & follow-up queue |

---

## 2. Setup Part A: Registration Sheet Webhook (60 Seconds)

### Step 1: Open Your Registration Sheet
Open your sheet in Google Chrome:
👉 **[Open RegistrationSheet](https://docs.google.com/spreadsheets/d/18ORNC2fzAbziNLsDUZ3u6VEh6_isZHOBNkuFg73t0a8/edit)**

### Step 2: Open Google Apps Script
In the top menu bar, click:
> **Extensions** $\to$ **Apps Script**

*(A new browser tab titled "Untitled project" or similar will open)*

---

### Step 3: Paste the Webhook Code
1. Delete any existing template code (`function myFunction() { ... }`).
2. Copy the code block below and paste it into the editor:

```javascript
/**
 * Blood Bank Automation Live Webhook
 * Handles direct real-time cell updates from Robot Framework / Python automation.
 */
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
    
    // Fallback columns for standard Registration Sheet layout
    if (statusCol === -1) statusCol = 18; // Column R
    if (dateCol === -1) dateCol = 19;     // Column S
    if (remarksCol === -1) remarksCol = 20; // Column T
    
    var targetRow = data.row ? Number(data.row) : null;
    var targetEmail = data.email ? String(data.email).trim().toLowerCase() : null;
    
    // Look up row by email if provided
    if (!targetRow && targetEmail && emailCol !== -1 && lastRow >= 2) {
      var emailValues = sheet.getRange(2, emailCol, lastRow - 1, 1).getValues();
      for (var r = 0; r < emailValues.length; r++) {
        if (String(emailValues[r][0] || "").trim().toLowerCase() === targetEmail) {
          targetRow = r + 2;
          break;
        }
      }
    }
    
    // Find next Pending or Blank row if row not specified
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

---

### Step 4: Deploy as Web App
1. In the top right corner, click the blue **`Deploy`** button $\to$ click **`New deployment`**.
2. Click the gear icon (⚙️) next to "Select type" $\to$ select **`Web app`**.
3. Configure the 3 fields:
   * **Description:** `Registration Webhook`
   * **Execute as:** `Me (your Google account)`
   * **Who has access:** ⚠️ **`Anyone`** *(Crucial: allows external test runners to send updates)*
4. Click **`Deploy`**.

---

### Step 5: Grant Google Authorization
Google will display an authorization prompt:
1. Click **Authorize access** $\to$ select your Google account.
2. Click **Advanced** (small text in bottom left corner).
3. Click **Go to Untitled project (unsafe)**.
4. Click **Allow**.

---

### Step 6: Copy Web App URL
Under **Web app URL**, click **Copy**:
```
https://script.google.com/macros/s/AKfycbx.../exec
```

---

### Step 7: Save in `automation/.env`
Open [`automation/.env`](file:///f:/Projects/blood_bank_management/automation/.env) and paste your URL:
```env
GOOGLE_REGISTRATION_WEBHOOK_URL=https://script.google.com/macros/s/AKfycbx.../exec
```

---

## 3. Setup Part B: Donor Motivation Sheet Webhook (Optional / Follow Same Steps)

If you also want automated write-backs for donor motivation emails:
1. Open your Donor Sheet in Chrome:
   👉 **[Open DonorQueue Sheet](https://docs.google.com/spreadsheets/d/1Z5OXbxG0ZWzlIxiyuMj4mTNB7mDsFGwBcEi1WnL5Nbw/edit)**
2. Click **Extensions** $\to$ **Apps Script**.
3. Paste the exact same code snippet from Step 3 above.
4. Click **Deploy** $\to$ **New deployment** $\to$ **Web app** $\to$ Set "Who has access" to **Anyone** $\to$ Click **Deploy**.
5. Copy the Web app URL and paste into [`automation/.env`](file:///f:/Projects/blood_bank_management/automation/.env):
```env
GOOGLE_DONOR_WEBHOOK_URL=https://script.google.com/macros/s/AKfycbz.../exec
```

---

## 4. Verification & Testing

### Instant 1-Click Verification Command
Once you save the URL in `automation/.env`, open your terminal and run:

```cmd
cd f:\Projects\blood_bank_management\automation
test_google_sheet.bat
```

> **What happens:**
> 1. The script pings your Webhook.
> 2. It sends an update to your online Google Sheet.
> 3. Switch to your Google Sheet in Chrome: **Row 8 Column R (`Status`) immediately changes to `Completed` with a light green background!**

---

## 5. How Tests Automatically Update the Google Sheet

Whenever you run any test:

```cmd
:: 1. Reads next pending row from sheet, registers role, marks 'Completed' in Google Sheet
run_excel_registration.bat

:: 2. Fills browser user signup form from sheet, marks 'Completed' in Google Sheet
run_ui_register.bat

:: 3. Logs in as Admin, creates bloodbank from sheet, marks 'Completed' in Google Sheet
run_ui_admin.bat
```

The test runner will:
1. Scan for the next row with `Status = "Pending"` or empty/blank.
2. Fill the form / execute the API registration.
3. Automatically trigger the webhook to write **`Status = Completed`**, **`Completed Date`**, and **`Remarks`** directly into your live Google Sheet in real time.


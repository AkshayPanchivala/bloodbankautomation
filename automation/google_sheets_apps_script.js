/**
 * ==============================================================================
 * GOOGLE APPS SCRIPT: LIVE ONLINE SPREADSHEET AUTOMATION WEBHOOK
 * ==============================================================================
 * 
 * This script runs directly inside your Google Sheet. When Robot Framework,
 * Python, or UI automation finishes a test case, it sends a quick HTTP request
 * here, and this script instantly updates the cell in your online Google Sheet
 * in real-time right in your browser!
 * 
 * ------------------------------------------------------------------------------
 * HOW TO INSTALL (Takes 1 Minute):
 * ------------------------------------------------------------------------------
 * 1. Open your Google Sheet in Google Chrome:
 *    https://docs.google.com/spreadsheets/d/18ORNC2fzAbziNLsDUZ3u6VEh6_isZHOBNkuFg73t0a8/edit
 * 
 * 2. In the top menu, click:
 *    Extensions  ->  Apps Script
 * 
 * 3. Delete any text currently in the Apps Script editor, and PASTE THIS ENTIRE FILE.
 * 
 * 4. Click the blue "Deploy" button (top right) -> "New deployment"
 * 
 * 5. Click the gear icon (⚙️) next to "Select type" -> Choose "Web app"
 * 
 * 6. Set the settings:
 *    - Description: "Live Automation Webhook"
 *    - Execute as: "Me" (your Google account)
 *    - Who has access: "Anyone" (allows the test runner to update the sheet)
 * 
 * 7. Click "Deploy" -> Click "Authorize access" -> Choose your Google account -> 
 *    Click "Advanced" -> Click "Go to Untitled project (unsafe)" -> Click "Allow".
 * 
 * 8. Copy the "Web app URL" (it looks like:
 *    https://script.google.com/macros/s/AKfycb.../exec)
 * 
 * 9. Paste this URL into your "automation/.env" file:
 *    GOOGLE_REGISTRATION_WEBHOOK_URL=https://script.google.com/macros/s/AKfycb.../exec
 * 
 * Done! Any test you run will now immediately update Row 8 (and any row)
 * directly inside your live Google Sheet in Chrome!
 * ==============================================================================
 */

function doPost(e) {
  var data = {};
  if (e && e.postData && e.postData.contents) {
    try {
      data = JSON.parse(e.postData.contents);
    } catch (err) {
      data = e.parameter || {};
    }
  } else if (e && e.parameter) {
    data = e.parameter;
  }
  return handleLiveUpdate(data);
}

function doGet(e) {
  var data = (e && e.parameter) ? e.parameter : {};
  if (data.row || data.email || data.status) {
    return handleLiveUpdate(data);
  }
  return ContentService.createTextOutput(JSON.stringify({
    status: "online",
    message: "Google Sheet Live Automation Webhook is READY & CONNECTED!",
    timestamp: new Date().toISOString()
  })).setMimeType(ContentService.MimeType.JSON);
}

function handleLiveUpdate(data) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheetName = data.sheet || "Registrations";
    var sheet = ss.getSheetByName(sheetName) || ss.getActiveSheet();
    
    var lastRow = sheet.getLastRow();
    var lastCol = sheet.getLastColumn();
    var headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
    
    // Find column positions dynamically from header row
    var statusCol = -1;
    var dateCol = -1;
    var remarksCol = -1;
    var emailCol = -1;
    
    for (var c = 0; c < headers.length; c++) {
      var h = String(headers[c] || "").trim().toLowerCase();
      if (h === "status") statusCol = c + 1;
      else if (h === "completed date" || h === "completed_date") dateCol = c + 1;
      else if (h === "remarks") remarksCol = c + 1;
      else if (h === "email") emailCol = c + 1;
    }
    
    // Default column numbers if headers not matched
    if (statusCol === -1) statusCol = 18; // Column R
    if (dateCol === -1) dateCol = 19;     // Column S
    if (remarksCol === -1) remarksCol = 20; // Column T
    
    var targetRow = data.row ? Number(data.row) : null;
    var targetEmail = data.email ? String(data.email).trim().toLowerCase() : null;
    
    // 1. Look up row by email if provided and row not provided
    if (!targetRow && targetEmail && emailCol !== -1 && lastRow >= 2) {
      var emailValues = sheet.getRange(2, emailCol, lastRow - 1, 1).getValues();
      for (var r = 0; r < emailValues.length; r++) {
        if (String(emailValues[r][0] || "").trim().toLowerCase() === targetEmail) {
          targetRow = r + 2;
          break;
        }
      }
    }
    
    // 2. If neither provided, find first Pending or Blank row
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
    
    // If targetRow found within bounds
    if (targetRow && targetRow <= lastRow) {
      var newStatus = data.status || "Completed";
      
      // Update Status Cell: Green Background and Bold Green Text
      var statusCell = sheet.getRange(targetRow, statusCol);
      statusCell.setValue(newStatus);
      statusCell.setBackground("#E8F5E9");
      statusCell.setFontColor("#2E7D32");
      statusCell.setFontWeight("bold");
      
      // Update Completed Date
      var tz = Session.getScriptTimeZone() || "GMT+5:30";
      var nowStr = data.completedDate || Utilities.formatDate(new Date(), tz, "yyyy-MM-dd HH:mm:ss");
      sheet.getRange(targetRow, dateCol).setValue(nowStr);
      
      // Update Remarks
      if (data.remarks) {
        sheet.getRange(targetRow, remarksCol).setValue(data.remarks);
      }
      
      // Force instant flush to live Google Sheet UI
      SpreadsheetApp.flush();
      
      return ContentService.createTextOutput(JSON.stringify({
        status: "success",
        updatedRow: targetRow,
        newStatus: newStatus,
        completedDate: nowStr,
        remarks: data.remarks || ""
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: "Row could not be determined or is out of bounds (targetRow=" + targetRow + ", lastRow=" + lastRow + ")"
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: err.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}


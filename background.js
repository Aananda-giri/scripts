// Background script to handle screenshot capture and PDF generation
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'captureTab') {
    try {
      chrome.tabs.captureVisibleTab(
        null,
        { format: 'png', quality: 90 },
        (dataUrl) => {
          if (chrome.runtime.lastError) {
            console.error('Screenshot error:', chrome.runtime.lastError);
            sendResponse({ error: chrome.runtime.lastError.message });
          } else if (dataUrl) {
            sendResponse({ dataUrl: dataUrl });
          } else {
            sendResponse({ error: 'No screenshot data received' });
          }
        }
      );
    } catch (error) {
      console.error('Capture error:', error);
      sendResponse({ error: error.message });
    }
    return true; // Keep the message channel open for async response
  }
  
  // Handle PDF generation request (currently not implemented due to complexity)
  // Background scripts have limited access to DOM APIs needed for PDF generation
  if (message.action === 'generatePDF') {
    console.log('PDF generation requested in background script, but not implemented');
    sendResponse({ success: false, reason: 'PDF generation in background not available' });
    return true;
  }
});
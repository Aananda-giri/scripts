// Content script for taking screenshots and scrolling
// Wrap in IIFE to prevent variable conflicts when injected multiple times
(function() {
  'use strict';
  
  // Check if our extension is already loaded
  if (window.screenshotScrollerLoaded) {
    console.log('Screenshot scroller already loaded, skipping');
    return;
  }
  
  window.screenshotScrollerLoaded = true;
  console.log('Content script loaded and ready');
  
  let isRunning = false;
  let screenshots = [];

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Content script received message:', message);
    
    if (message.action === 'startScreenshots' && !isRunning) {
      startScreenshotProcess(message.delay, message.scrollAmount, message.outputFormat || 'html');
      sendResponse({ status: 'started' });
    }
    
    return true; // Keep the message channel open
  });

  async function startScreenshotProcess(delay, scrollAmount, outputFormat = 'html') {
    isRunning = true;
    screenshots = [];
    
    try {
      // Scroll to top first
      window.scrollTo(0, 0);
      await wait(1000); // Wait for page to settle
      
      let screenshotCount = 0;
      let previousScrollTop = -1;
      let stuckCount = 0;
      const maxScreenshots = 100; // Safety limit
      
      while (screenshotCount < maxScreenshots) {
        screenshotCount++;
        const currentScrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Send progress update
        chrome.runtime.sendMessage({
          action: 'updateProgress',
          current: screenshotCount
        });
        
        // Take screenshot first
        try {
          const screenshotData = await captureVisibleTab();
          screenshots.push(screenshotData);
        } catch (error) {
          console.error('Error taking screenshot:', error);
          chrome.runtime.sendMessage({
            action: 'error',
            error: 'Failed to take screenshot: ' + error.message
          });
          isRunning = false;
          return;
        }
        
        // Calculate page dimensions
        const windowHeight = window.innerHeight;
        const documentHeight = Math.max(
          document.body.scrollHeight,
          document.body.offsetHeight,
          document.documentElement.clientHeight,
          document.documentElement.scrollHeight,
          document.documentElement.offsetHeight
        );
        
        console.log(`Screenshot ${screenshotCount}: scrollTop=${currentScrollTop}, windowHeight=${windowHeight}, docHeight=${documentHeight}`);
        
        // Try to scroll down BEFORE checking if we're at bottom
        const beforeScrollTop = window.pageYOffset || document.documentElement.scrollTop;
        window.scrollBy(0, scrollAmount);
        
        // Wait for scroll to complete
        await wait(300);
        
        const afterScrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const actualScrollDistance = afterScrollTop - beforeScrollTop;
        
        console.log(`Scroll attempt: before=${beforeScrollTop}, after=${afterScrollTop}, distance=${actualScrollDistance}`);
        
        // Check if we actually moved
        if (actualScrollDistance < 10) { // Less than 10px movement
          stuckCount++;
          console.log(`Scroll stuck count: ${stuckCount}`);
        } else {
          stuckCount = 0; // Reset if we successfully scrolled
        }
        
        // Multiple ways to detect end of page
        const isAtBottom = (afterScrollTop + windowHeight) >= (documentHeight - 50); // 50px tolerance
        const scrollIsStuck = stuckCount >= 3; // Failed to scroll 3 times in a row
        
        if (scrollIsStuck) {
          console.log('Stopping: Scroll position stuck');
          break;
        }
        
        if (isAtBottom) {
          console.log('Stopping: Reached bottom of page');
          break;
        }
        
        // Update previous position
        previousScrollTop = afterScrollTop;
        
        // Wait for specified delay (minus the 300ms we already waited)
        await wait(Math.max(delay - 300, 100));
      }
      
      if (screenshotCount >= maxScreenshots) {
        console.log('Stopping: Reached maximum screenshot limit');
      }
      
      console.log(`Total screenshots taken: ${screenshots.length}`);
      
      // Generate output based on user preference
      if (outputFormat === 'pdf') {
        await generatePDF();
      } else {
        createHTMLDownload();
      }
      
      chrome.runtime.sendMessage({
        action: 'completed',
        total: screenshots.length
      });
      
    } catch (error) {
      console.error('Error in screenshot process:', error);
      chrome.runtime.sendMessage({
        action: 'error',
        error: error.message
      });
    } finally {
      isRunning = false;
    }
  }

  function captureVisibleTab() {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage({
        action: 'captureTab'
      }, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else if (response && response.dataUrl) {
          resolve(response.dataUrl);
        } else if (response && response.error) {
          reject(new Error(response.error));
        } else {
          reject(new Error('Unknown error capturing screenshot'));
        }
      });
    });
  }

  async function generatePDF() {
    console.log('Starting PDF generation with screenshots:', screenshots.length);
    
    // Since CSP often blocks external scripts, we'll show a warning and fall back to HTML
    try {
      // Try to load jsPDF from a CDN (this will likely fail due to CSP)
      await loadPDFLibrary();
      
      if (window.jspdf) {
        await createActualPDF();
        return;
      }
    } catch (error) {
      console.log('PDF library loading failed (likely due to CSP), falling back to HTML:', error);
    }
    
    // Fallback: Create HTML file and inform user
    createHTMLDownload();
    chrome.runtime.sendMessage({
      action: 'showInstructions',
      message: 'Note: Direct PDF generation blocked by website security. HTML file created instead - easily convert to PDF with Ctrl+P!'
    });
  }

  function loadPDFLibrary() {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
      script.onload = () => {
        setTimeout(() => {
          if (window.jspdf) {
            resolve();
          } else {
            reject(new Error('jsPDF not available'));
          }
        }, 100);
      };
      script.onerror = () => reject(new Error('Failed to load jsPDF'));
      document.head.appendChild(script);
      
      // Timeout after 5 seconds
      setTimeout(() => reject(new Error('Timeout loading jsPDF')), 5000);
    });
  }

  async function createActualPDF() {
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF();
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    
    return new Promise((resolve) => {
      let processedImages = 0;
      
      for (let i = 0; i < screenshots.length; i++) {
        if (i > 0) {
          pdf.addPage();
        }
        
        const img = new Image();
        img.onload = function() {
          try {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            const aspectRatio = img.width / img.height;
            let imgWidth = pageWidth - 20;
            let imgHeight = imgWidth / aspectRatio;
            
            if (imgHeight > pageHeight - 20) {
              imgHeight = pageHeight - 20;
              imgWidth = imgHeight * aspectRatio;
            }
            
            canvas.width = imgWidth;
            canvas.height = imgHeight;
            ctx.drawImage(img, 0, 0, imgWidth, imgHeight);
            
            const imgData = canvas.toDataURL('image/jpeg', 0.8);
            pdf.addImage(imgData, 'JPEG', 10, 10, imgWidth, imgHeight);
            
            processedImages++;
            if (processedImages === screenshots.length) {
              const pdfBlob = pdf.output('blob');
              const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
              const filename = `${document.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}-${timestamp}.pdf`;
              downloadBlob(pdfBlob, filename);
              resolve();
            }
          } catch (error) {
            console.error('Error processing image:', error);
            processedImages++;
            if (processedImages === screenshots.length) {
              resolve();
            }
          }
        };
        img.onerror = function() {
          processedImages++;
          if (processedImages === screenshots.length) {
            resolve();
          }
        };
        img.src = screenshots[i];
      }
    });
  }

  // Create a downloadable HTML file with all screenshots
  function createHTMLDownload() {
    console.log('Creating HTML download with screenshots');
    
    // Create HTML content with all screenshots
    let htmlContent = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>${document.title}</title>
  <style>
    body { 
      margin: 0; 
      padding: 20px; 
      font-family: Arial, sans-serif; 
      background: #f5f5f5;
    }
    .header {
      background: white;
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 20px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .screenshot-container { 
      background: white;
      margin-bottom: 20px; 
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      overflow: hidden;
      page-break-after: always;
    }
    .screenshot-info { 
      padding: 15px;
      background: #f8f9fa;
      border-bottom: 1px solid #dee2e6;
      font-weight: bold; 
      color: #495057;
    }
    .screenshot-container img { 
      width: 100%; 
      height: auto; 
      display: block;
    }
    .instructions {
      background: #d4edda;
      border: 1px solid #c3e6cb;
      border-radius: 8px;
      padding: 15px;
      margin-bottom: 20px;
    }
    .instructions h3 {
      margin-top: 0;
      color: #155724;
    }
    .instructions p {
      margin-bottom: 5px;
      color: #155724;
    }
    @media print { 
      body { background: white; margin: 0; padding: 10px; }
      .header { box-shadow: none; }
      .screenshot-container { 
        page-break-inside: avoid; 
        box-shadow: none;
        border: 1px solid #ddd;
      } 
      .instructions { display: none; }
    }
  </style>
</head>
<body>`;

    for (let i = 0; i < screenshots.length; i++) {
      htmlContent += `
  <div class="screenshot-container">
    <img src="${screenshots[i]}" alt="Screenshot ${i + 1}" loading="lazy" />
  </div>`;
    }

    htmlContent += `
</body>
</html>`;

    // Create and download HTML file
    const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    const filename = `${document.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}-${timestamp}.html`;
    
    downloadBlob(blob, filename);
    
    // Notify user
    chrome.runtime.sendMessage({
      action: 'showInstructions',
      message: `HTML file downloaded! Open it and press Ctrl+P to save as PDF. (${screenshots.length} screenshots captured)`
    });
  }

  async function createPDF() {
    // This function is no longer used due to CSP restrictions
    // Keeping for potential future use if we move PDF generation to background script
    console.log('createPDF function called but not implemented due to CSP restrictions');
  }

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

})(); // End of IIFE
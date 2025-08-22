document.addEventListener('DOMContentLoaded', function() {
  const startBtn = document.getElementById('startBtn');
  const delayInput = document.getElementById('delay');
  const scrollAmountInput = document.getElementById('scrollAmount');
  const statusDiv = document.getElementById('status');

  startBtn.addEventListener('click', async function() {
    const delay = parseInt(delayInput.value) * 1000; // Convert to milliseconds
    const scrollAmount = parseInt(scrollAmountInput.value);
    const outputFormat = document.getElementById('outputFormat').value;
    
    startBtn.disabled = true;
    startBtn.textContent = 'Processing...';
    showStatus('Starting screenshot process...', 'running');
    
    try {
      // Get current active tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      // Always inject the content script to ensure it's loaded
      try {
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content.js']
        });
        console.log('Content script injected successfully');
      } catch (scriptError) {
        console.error('Script injection failed:', scriptError);
        showStatus('Error: Cannot inject script. Please refresh the page and try again.', 'completed');
        resetButton();
        return;
      }
      
      // Wait a bit for the content script to initialize
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Send message to content script to start the process
      try {
        await new Promise((resolve, reject) => {
          chrome.tabs.sendMessage(tab.id, {
            action: 'startScreenshots',
            delay: delay,
            scrollAmount: scrollAmount,
            outputFormat: outputFormat
          }, (response) => {
            if (chrome.runtime.lastError) {
              reject(new Error(chrome.runtime.lastError.message));
            } else {
              resolve(response);
            }
          });
        });
        console.log('Message sent successfully');
      } catch (messageError) {
        console.error('Message send error:', messageError);
        showStatus('Error: Could not communicate with page. Please refresh and try again.', 'completed');
        resetButton();
        return;
      }
      
    } catch (error) {
      console.error('Error:', error);
      showStatus('Error starting process: ' + error.message, 'completed');
      resetButton();
    }
  });
  
  // Listen for messages from content script
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'updateProgress') {
      showStatus(`Taking screenshot ${message.current}...`, 'running');
    } else if (message.action === 'completed') {
      showStatus(`Completed! ${message.total} screenshots taken. Generating PDF...`, 'completed');
      resetButton();
    } else if (message.action === 'error') {
      showStatus(`Error: ${message.error}`, 'completed');
      resetButton();
    } else if (message.action === 'showInstructions') {
      showStatus(message.message, 'completed');
      resetButton();
    }
  });
  
  function showStatus(text, type) {
    statusDiv.textContent = text;
    statusDiv.className = `status ${type}`;
    statusDiv.style.display = 'block';
  }
  
  function resetButton() {
    startBtn.disabled = false;
    startBtn.textContent = 'Start Screenshot Scroll';
  }
});
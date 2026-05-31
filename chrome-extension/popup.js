// popup.js

function log(msg, type = 'info') {
  const logEl = document.getElementById('log');
  const line = document.createElement('div');
  line.className = type;
  line.textContent = '> ' + msg;
  logEl.appendChild(line);
  logEl.scrollTop = logEl.scrollHeight;
}

async function loadStatus() {
  chrome.runtime.sendMessage({ action: 'getStoredData' }, (data) => {
    const sessionEl = document.getElementById('status-session');
    const timeEl = document.getElementById('status-time');

    if (data && data.sessionid) {
      sessionEl.textContent = '✅ שמור';
      sessionEl.className = 'status-value ok';
      if (data.last_captured) {
        const d = new Date(data.last_captured);
        timeEl.textContent = d.toLocaleString('he-IL');
      }
    } else {
      sessionEl.textContent = '❌ לא שמור';
      sessionEl.className = 'status-value error';
    }
  });
}

document.getElementById('btn-capture').addEventListener('click', () => {
  log('מנסה לתפוס קוקיז...', 'info');
  chrome.runtime.sendMessage({ action: 'getCookies' }, (response) => {
    if (response && response.success) {
      log('קוקיז נשמרו בהצלחה! ✅', 'success');
      loadStatus();
    } else {
      log('שגיאה - האם אתה מחובר לאתר?', 'error');
      log('פתח את app.shiftorganizer.com ונסה שוב', 'info');
    }
  });
});

document.getElementById('btn-test').addEventListener('click', () => {
  log('בודק חיבור ל-API...', 'info');
  chrome.storage.local.get(['sessionid', 'csrftoken'], async (data) => {
    if (!data.sessionid) {
      log('אין קוקיז - לחץ "תפוס קוקיז" קודם', 'error');
      return;
    }
    
    try {
      const resp = await fetch('https://app.shiftorganizer.com/api/shifts/', {
        headers: {
          'Cookie': `sessionid=${data.sessionid}; csrftoken=${data.csrftoken}`,
          'X-Csrftoken': data.csrftoken
        },
        credentials: 'include'
      });
      
      if (resp.ok) {
        const json = await resp.json();
        log(`API עובד! קיבלנו ${JSON.stringify(json).length} תווים`, 'success');
      } else {
        log(`שגיאת API: ${resp.status} - נסה לתפוס קוקיז מחדש`, 'error');
      }
    } catch (e) {
      log('שגיאת רשת: ' + e.message, 'error');
    }
  });
});

document.getElementById('btn-copy').addEventListener('click', () => {
  chrome.storage.local.get(['sessionid', 'csrftoken'], (data) => {
    if (!data.sessionid) {
      log('אין קוקיז לעתק!', 'error');
      return;
    }
    
    const text = `SESSIONID=${data.sessionid}\nCSRFTOKEN=${data.csrftoken}`;
    navigator.clipboard.writeText(text).then(() => {
      log('הועתק! הדבק ב-.env שלך', 'success');
    }).catch(() => {
      log('sessionid: ' + data.sessionid.substring(0, 10) + '...', 'info');
      log('csrftoken: ' + data.csrftoken.substring(0, 10) + '...', 'info');
    });
  });
});

loadStatus();

// background.js - שומר קוקיז בכל פעם שמבקרים באתר

chrome.webRequest && chrome.webRequest.onSendHeaders && chrome.webRequest.onSendHeaders.addListener(
  function(details) {
    const cookieHeader = details.requestHeaders.find(h => h.name.toLowerCase() === 'cookie');
    const csrfHeader = details.requestHeaders.find(h => h.name.toLowerCase() === 'x-csrftoken');
    
    if (cookieHeader) {
      const cookies = parseCookies(cookieHeader.value);
      if (cookies.sessionid && cookies.csrftoken) {
        chrome.storage.local.set({
          sessionid: cookies.sessionid,
          csrftoken: cookies.csrftoken,
          last_captured: new Date().toISOString()
        }, () => {
          console.log('✅ TabitShift cookies saved:', new Date().toLocaleString());
        });
      }
    }
  },
  { urls: ["https://app.shiftorganizer.com/api/*"] },
  ["requestHeaders"]
);

function parseCookies(cookieString) {
  const cookies = {};
  cookieString.split(';').forEach(cookie => {
    const [key, ...val] = cookie.trim().split('=');
    cookies[key.trim()] = val.join('=').trim();
  });
  return cookies;
}

// הוסף הרשאת webRequest ב-manifest אם צריך
// לחילופין - גישה ישירה לקוקיז דרך chrome.cookies API
async function captureViaAPI() {
  try {
    const sessionCookie = await chrome.cookies.get({
      url: "https://app.shiftorganizer.com",
      name: "sessionid"
    });
    const csrfCookie = await chrome.cookies.get({
      url: "https://app.shiftorganizer.com", 
      name: "csrftoken"
    });

    if (sessionCookie && csrfCookie) {
      await chrome.storage.local.set({
        sessionid: sessionCookie.value,
        csrftoken: csrfCookie.value,
        last_captured: new Date().toISOString()
      });
      return { sessionid: sessionCookie.value, csrftoken: csrfCookie.value };
    }
    return null;
  } catch (e) {
    console.error('Error capturing cookies:', e);
    return null;
  }
}

// הקשב להודעות מה-popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'getCookies') {
    captureViaAPI().then(cookies => {
      sendResponse({ success: !!cookies, cookies });
    });
    return true; // async
  }
  
  if (message.action === 'getStoredData') {
    chrome.storage.local.get(['sessionid', 'csrftoken', 'last_captured'], (data) => {
      sendResponse(data);
    });
    return true;
  }
});

// הודעה כשהאקסטנשן מותקן
chrome.runtime.onInstalled.addListener(() => {
  console.log('TabitShift Sync Extension installed!');
});

"""
tabit_sync.py - מסנכרן משמרות מ-TabitShift לגוגל קלנדר
הרץ כל שבת 17:00 דרך Windows Task Scheduler
"""

import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# ==================== הגדרות ====================
load_dotenv()

EMPLOYEE_ID = 785043          # ה-ID של אלון סימה
MY_NAME = "אלון סימה"

SESSIONID = os.getenv("SESSIONID")
CSRFTOKEN = os.getenv("CSRFTOKEN")

CALENDAR_ID = "primary"       # הקלנדר הראשי - אפשר לשנות ל-ID ספציפי
SCOPES = ['https://www.googleapis.com/auth/calendar']

# כמה שבועות קדימה לסנכרן
WEEKS_AHEAD = 2

# ==================== TabitShift API ====================

def get_headers():
    return {
        "Cookie": f"sessionid={SESSIONID}; csrftoken={CSRFTOKEN}; django_language=he",
        "X-Csrftoken": CSRFTOKEN,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://app.shiftorganizer.com/app/rota",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

def get_rotas_for_week(date_str):
    """מקבל את רשימת ה-rotas לשבוע נתון"""
    url = f"https://app.shiftorganizer.com/api/rotas/?date={date_str}&application=5652"
    resp = requests.get(url, headers=get_headers())
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"  ❌ שגיאה בקבלת rotas ל-{date_str}: {resp.status_code}")
        return []

def get_cells_for_rota(rota_id):
    """מקבל את כל התאים (משמרות) ל-rota ספציפי"""
    url = f"https://app.shiftorganizer.com/api/cells/?rota={rota_id}"
    resp = requests.get(url, headers=get_headers())
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"  ❌ שגיאה בקבלת cells ל-rota {rota_id}: {resp.status_code}")
        return []

def get_my_shifts():
    """מקבל את כל המשמרות שלי בN שבועות הקרובים"""
    my_shifts = []
    today = datetime.now()
    
    print(f"🔍 מחפש משמרות ל-{WEEKS_AHEAD} שבועות קרובים...")
    
    for week in range(WEEKS_AHEAD):
        # מחשב את יום ראשון של כל שבוע
        week_start = today - timedelta(days=today.weekday() + 1) + timedelta(weeks=week)
        # מחפש את יום ראשון (weekday 6 = Sunday)
        days_until_sunday = (6 - week_start.weekday()) % 7
        sunday = week_start + timedelta(days=days_until_sunday)
        date_str = sunday.strftime("%Y-%m-%d")
        
        print(f"  📅 שבוע {week+1}: {date_str}")
        
        rotas = get_rotas_for_week(date_str)
        
        for rota in rotas:
            rota_id = rota.get('id')
            if not rota_id:
                continue
                
            cells = get_cells_for_rota(rota_id)
            
            for cell in cells:
                if cell.get('employee') == EMPLOYEE_ID and not cell.get('is_deleted'):
                    my_shifts.append(cell)
    
    print(f"✅ נמצאו {len(my_shifts)} משמרות")
    return my_shifts

# ==================== Google Calendar ====================

def get_google_service():
    """מתחבר לגוגל קלנדר עם OAuth"""
    creds = None
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('calendar', 'v3', credentials=creds)

def get_existing_events(service, start_date, end_date):
    """מקבל אירועים קיימים בגוגל קלנדר"""
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start_date.isoformat() + 'Z',
        timeMax=end_date.isoformat() + 'Z',
        q="משמרת",  # מחפש רק אירועים שיצרנו
        singleEvents=True
    ).execute()
    return events_result.get('items', [])

def shift_to_event(shift):
    """ממיר משמרת מ-TabitShift לפורמט גוגל קלנדר"""
    date = shift['date']
    start_full = shift['planned_start_full']
    end_full = shift['planned_end_full']
    
    # שם האירוע
    start_time = shift['planned_start'][:5]  # HH:MM
    end_time = shift['planned_end'][:5]
    title = f"🔄 משמרת {start_time}-{end_time}"
    
    return {
        'summary': title,
        'description': f"משמרת TabitShift\nעובד: {MY_NAME}\nID: {shift['id']}",
        'start': {
            'dateTime': start_full,
            'timeZone': 'Asia/Jerusalem',
        },
        'end': {
            'dateTime': end_full,
            'timeZone': 'Asia/Jerusalem',
        },
        'colorId': '6',  # ירוק טורקיז
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 60},
            ],
        },
    }

def sync_shifts_to_calendar(service, shifts):
    """מסנכרן משמרות לגוגל קלנדר"""
    if not shifts:
        print("⚠️ אין משמרות לסנכרן")
        return
    
    added = 0
    skipped = 0
    
    # מחפש אירועים קיימים
    start_range = datetime.now() - timedelta(weeks=2)
    end_range = datetime.now() + timedelta(weeks=WEEKS_AHEAD)
    existing = get_existing_events(service, start_range, end_range)
    
    # מחלץ ID-ים של משמרות שכבר הוספנו
    existing_shift_ids = set()
    for ev in existing:
        desc = ev.get('description', '')
        if 'ID:' in desc:
            try:
                shift_id = int(desc.split('ID:')[1].strip().split('\n')[0])
                existing_shift_ids.add(shift_id)
            except:
                pass
    
    print(f"📋 {len(existing_shift_ids)} משמרות כבר בקלנדר")
    
    for shift in shifts:
        shift_id = shift['id']
        
        if shift_id in existing_shift_ids:
            print(f"  ⏭️  משמרת {shift['date']} {shift['planned_start'][:5]} - כבר קיימת")
            skipped += 1
            continue
        
        event = shift_to_event(shift)
        
        try:
            service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
            print(f"  ✅ נוסף: {shift['date']} {shift['planned_start'][:5]}-{shift['planned_end'][:5]}")
            added += 1
        except Exception as e:
            print(f"  ❌ שגיאה בהוספת {shift['date']}: {e}")
    
    print(f"\n📊 סיכום: {added} נוספו, {skipped} דולגו")

# ==================== Main ====================

def main():
    print("=" * 50)
    print(f"🚀 TabitShift → Google Calendar Sync")
    print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 50)
    
    # בדיקת קוקיז
    if not SESSIONID or not CSRFTOKEN:
        print("❌ חסרים SESSIONID ו-CSRFTOKEN!")
        print("   פתח את Chrome Extension ולחץ 'תפוס קוקיז'")
        print("   אחר כך העתק ל-.env")
        return
    
    print(f"👤 מסנכרן משמרות של: {MY_NAME} (ID: {EMPLOYEE_ID})")
    
    # שלב 1: קבל משמרות מ-TabitShift
    shifts = get_my_shifts()
    
    if not shifts:
        print("⚠️ לא נמצאו משמרות - בדוק חיבור ו-cookies")
        return
    
    # שלב 2: התחבר לגוגל קלנדר
    print("\n🔐 מתחבר לגוגל קלנדר...")
    service = get_google_service()
    print("✅ מחובר!")
    
    # שלב 3: סנכרן
    print("\n📅 מסנכרן לגוגל קלנדר...")
    sync_shifts_to_calendar(service, shifts)
    
    print("\n✨ הסנכרון הושלם!")

if __name__ == "__main__":
    main()

# TabitShift → Google Calendar Sync

מסנכרן אוטומטי משמרות מ-TabitShift לגוגל קלנדר כל שבת ב-17:00

---

## מבנה הפרויקט

```
tabit-sync/
├── chrome-extension/       ← האקסטנשן לתפיסת cookies
│   ├── manifest.json
│   ├── background.js
│   ├── popup.html
│   └── popup.js
└── python-script/          ← הסקריפט הראשי
    ├── tabit_sync.py
    ├── .env                ← הקוקיז שלך (לא לשתף!)
    ├── requirements.txt
    └── setup_scheduler.bat ← הגדרת אוטומציה
```

---

## התקנה - שלב אחר שלב

### שלב 1: התקן ספריות Python

פתח CMD והרץ:
```
pip install -r requirements.txt
```

### שלב 2: התקן את Chrome Extension

1. פתח Chrome → `chrome://extensions/`
2. הפעל **Developer mode** (מתג למעלה-ימין)
3. לחץ **Load unpacked**
4. בחר את תיקיית `chrome-extension`
5. האקסטנשן יופיע בסרגל הכלים

### שלב 3: תפוס את הקוקיז

1. כנס ל-`app.shiftorganizer.com` והתחבר
2. לחץ על האייקון של האקסטנשן
3. לחץ **"תפוס קוקיז מהאתר"**
4. לחץ **"העתק קוקיז לסקריפט"**
5. פתח את `.env` והדבק את הערכים

### שלב 4: הגדר Google Calendar

1. הנח את `credentials.json` (מגוגל קלאוד) בתיקיית `python-script`
2. הרץ פעם ראשונה:
   ```
   python tabit_sync.py
   ```
3. יפתח דפדפן לאישור הרשאות גוגל - אשר
4. ייצור קובץ `token.pickle` אוטומטית

### שלב 5: הגדר אוטומציה שבועית

1. לחץ ימני על `setup_scheduler.bat`
2. בחר **"הפעל כמנהל מערכת"**
3. זהו! הסקריפט ירוץ כל שבת 17:00

---

## עדכון קוקיז (כשפג תוקף)

הקוקיז מתחדשים אוטומטית כל עוד אתה מחובר לאתר.
אם הסקריפט נכשל - חזור על שלב 3.

---

## בדיקה ידנית

```
python tabit_sync.py
```

---

## פרטים טכניים

- **API URL:** `https://app.shiftorganizer.com/api/`
- **Employee ID:** 785043
- **אימות:** Cookie-based (sessionid + csrftoken)
- **קלנדר:** Primary Google Calendar
- **תזמון:** Windows Task Scheduler, כל שבת 17:00

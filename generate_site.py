import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from jinja2 import Environment, FileSystemLoader

# 🔧 Beállítás
SERVICE_ACCOUNT_FILE = 'credentials.json'
FOLDER_ID = '1RCnd1OUTP2NzO62fOTtgwZZ32TwWRhvr'
OUTPUT_DIR = 'output'

# Autentikáció
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build('drive', 'v3', credentials=creds)

# Lekérdezzük a fájlokat
results = service.files().list(
    q=f"'{FOLDER_ID}' in parents and trashed = false",
    fields="files(id, name, mimeType, webViewLink)",
).execute()

files = results.get('files', [])

# Csoportosítás tematikusan (mappa neve szerint)
folders = {}
for f in files:
    if f['mimeType'] == 'application/vnd.google-apps.folder':
        folders[f['id']] = {'name': f['name'], 'files': []}

# Második kör: fájlokat rendeljük hozzá a mappákhoz
for folder_id in folders.keys():
    subfiles = service.files().list(
        q=f"'{folder_id}' in parents and trashed = false",
        fields="files(id, name, webViewLink, mimeType)",
    ).execute().get('files', [])
    # Sort subfiles by name (ascending)
    subfiles.sort(key=lambda x: x['name'])
    folders[folder_id]['files'].extend(subfiles)

# Jinja HTML generálás
env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('base.html')

rendered = template.render(folders=folders.values())

# HTML mentése
os.makedirs(OUTPUT_DIR, exist_ok=True)
with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w') as f:
    f.write(rendered)

print("✔ Kész az index.html.")


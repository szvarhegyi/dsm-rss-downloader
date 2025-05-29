import requests
import feedparser
import hashlib
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

# ====== BEÁLLÍTÁSOK =======
DSM_HOST = os.getenv('DSM_HOST') 
USERNAME = os.getenv('DSM_USERNAME') 
PASSWORD = os.getenv('DSM_PASSWORD') 
DATABASE_DIRECTORY = os.getenv('STORAGE_DIR', '/app/storage') 
FEED_FILE = os.getenv('FEED_FILE', '/app/config/feed.json')

def get_sid():
    url = f"{DSM_HOST}/webapi/auth.cgi"
    params = {
        "api": "SYNO.API.Auth",
        "version": "6",
        "method": "login",
        "account": USERNAME,
        "passwd": PASSWORD,
        "session": "DownloadStation",
        "format": "sid"
    }
    r = requests.get(url, params=params, verify=False)
    r.raise_for_status()
    return r.json()["data"]["sid"]

def add_torrent(sid, torrent_url, destination):
    url = f"{DSM_HOST}/webapi/DownloadStation/task.cgi"
    params = {
        "api": "SYNO.DownloadStation.Task",
        "version": "1",
        "method": "create",
        "uri": torrent_url,
        "destination": destination,
        "_sid": sid
    }
    r = requests.post(url, data=params, verify=False)
    r.raise_for_status()
    print(r.content)
    print(f"[OK] Hozzáadva: {torrent_url}")

# ====== RSS OLVASÁS ÉS SZŰRÉS =======
def load_seen(seen_file):
    if os.path.exists(seen_file):
        with open(seen_file, "r") as f:
            return set(json.load(f))
    return set()

def load_feeds():
    if os.path.exists(FEED_FILE):
        with open(FEED_FILE, "r") as f:
            return json.load(f)
    return set()

def save_seen(seen, seen_file):
    with open(seen_file, "w") as f:
        json.dump(list(seen), f)

def get_item_id(entry):
    return hashlib.sha1(entry.link.encode()).hexdigest()

def process_feed(seen_file, rss, dest):
    print("[INFO] RSS olvasás...")
    feed = feedparser.parse(rss)
    seen = load_seen(seen_file)
    sid = get_sid()
    new_seen = set(seen)

    for entry in feed.entries:
        item_id = get_item_id(entry)
        if item_id not in seen:
            print(f"[ÚJ] {entry.title}")
            add_torrent(sid, entry.link, dest)
            new_seen.add(item_id)
    
    save_seen(new_seen, seen_file)

def process_feeds():
    feeds = load_feeds()
    for type in feeds:
        seen_file = os.path.join(DATABASE_DIRECTORY, type + '_seen.json')
        rss_feed_url = feeds.get(type).get('rss')
        destination = feeds.get(type).get('destination')
        process_feed(seen_file, rss_feed_url, destination)
    

# ====== FUTTATÁS =======
if __name__ == "__main__":
    INTERVAL_SECONDS = 60  # 1 percenként újra
    while True:
        try:
            process_feeds()
        except Exception as e:
            print(f"[HIBA] {e}")
        time.sleep(INTERVAL_SECONDS)
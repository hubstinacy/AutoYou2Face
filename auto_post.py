"""
AutoYou2Face - YouTube to Facebook Automated Publisher
Copyright (c) 2026 Hubstinacy / Grégory Hubin (aka The Nasty Mariol)
All Rights Reserved.

Official Brand: AutoYou2Face
Developer: Grégory Hubin (The Nasty Mariol) / Hubstinacy
"""

import os
import random
import json
import requests

# ----------------------------------------------------
# CONFIGURATION & CHARGEMENT
# ----------------------------------------------------
def load_config():
    config = {}
    if os.path.exists("config.txt"):
        try:
            with open("config.txt", "r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        key, value = line.strip().split("=", 1)
                        config[key.strip()] = value.strip()
        except Exception as e:
            print(f"⚠️ Erreur de lecture config.txt: {e}")

    youtube_key = config.get("YOUTUBE_API_KEY") or os.getenv("YOUTUBE_API_KEY")
    channel_id = config.get("YOUTUBE_CHANNEL_ID") or os.getenv("YOUTUBE_CHANNEL_ID")
    meta_token = config.get("META_ACCESS_TOKEN") or os.getenv("META_ACCESS_TOKEN")
    page_id = config.get("FB_PAGE_ID") or os.getenv("FB_PAGE_ID")

    return youtube_key, channel_id, meta_token, page_id

YOUTUBE_API_KEY, YOUTUBE_CHANNEL_ID, META_ACCESS_TOKEN, FB_PAGE_ID = load_config()
HISTORY_FILE = "posted_videos.json"

# ----------------------------------------------------
# LOGIQUE DU SERVICE AUTOYOU2FACE
# ----------------------------------------------------
def get_youtube_videos():
    videos = []
    next_page_token = ""
    while True:
        url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={YOUTUBE_CHANNEL_ID}&part=snippet,id&order=date&maxResults=50&pageToken={next_page_token}"
        res = requests.get(url).json()
        for item in res.get("items", []):
            if item.get("id", {}).get("kind") == "youtube#video":
                video_id = item["id"]["videoId"]
                videos.append({
                    "id": video_id,
                    "title": item["snippet"]["title"],
                    "url": f"https://www.youtube.com/watch?v={video_id}"
                })
        next_page_token = res.get("nextPageToken")
        if not next_page_token:
            break
    return videos

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def post_to_facebook(video):
    message = f"🎶 {video['title']}\n\nDécouvrez cette vidéo sur la chaîne :\n{video['url']}"
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
    payload = {
        "message": message,
        "link": video["url"],
        "access_token": META_ACCESS_TOKEN
    }
    res = requests.post(url, data=payload).json()
    if "id" in res:
        print("✅ [AutoYou2Face] Publié sur Facebook avec succès !")
    else:
        print(f"⚠️ [AutoYou2Face] Échec Facebook : {res}")

if __name__ == "__main__":
    print("🚀 [AutoYou2Face] Démarrage de l'application...")
    print("Developed by Grégory Hubin (The Nasty Mariol) / Hubstinacy")

    if not YOUTUBE_API_KEY or not YOUTUBE_CHANNEL_ID or not META_ACCESS_TOKEN or not FB_PAGE_ID:
        print("❌ Configuration incomplète. Renseignez config.txt ou vos GitHub Secrets.")
        exit(1)

    all_videos = get_youtube_videos()
    if not all_videos:
        print("❌ Aucune vidéo trouvée sur la chaîne YouTube.")
        exit(0)

    history = load_history()
    if len(history) >= len(all_videos):
        print("🔄 Cycle terminé ! Réinitialisation de l'historique.")
        history = []

    available_videos = [v for v in all_videos if v["id"] not in history]
    selected_video = random.choice(available_videos)
    print(f"📌 Vidéo sélectionnée ({len(history) + 1}/{len(all_videos)}) : {selected_video['title']}")

    post_to_facebook(selected_video)

    history.append(selected_video["id"])
    save_history(history)
    print("💾 Historique mis à jour.")

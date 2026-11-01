import os
import json
import random
import requests

# 1. Chargement des identifiants (Variables d'environnement GitHub Actions ou fichier config.txt)
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = os.environ.get("YOUTUBE_CHANNEL_ID")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")

HISTORY_FILE = "posted_videos.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def get_channel_videos():
    """Récupère jusqu'à 50 vidéos récentes de la chaîne YouTube."""
    url = (
        f"https://www.googleapis.com/youtube/v3/search"
        f"?key={YOUTUBE_API_KEY}"
        f"&channelId={YOUTUBE_CHANNEL_ID}"
        f"&part=snippet,id"
        f"&order=date"
        f"&maxResults=50"
        f"&type=video"
    )
    res = requests.get(url)
    if res.status_code != 200:
        print(f"❌ Erreur API YouTube: {res.status_code} - {res.text}")
        return []
    
    data = res.json()
    videos = []
    for item in data.get("items", []):
        vid_id = item["id"].get("videoId")
        title = item["snippet"]["title"]
        if vid_id:
            videos.append({"id": vid_id, "title": title})
    return videos

def post_to_facebook(video):
    video_url = f"https://www.youtube.com/watch?v={video['id']}"
    message = f"🎥 Nouvel extrait musical / Vidéo : {video['title']}\n\n👉 Regarder ici : {video_url}"
    
    fb_url = f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}/feed"
    payload = {
        "message": message,
        "link": video_url,
        "access_token": META_ACCESS_TOKEN
    }
    
    res = requests.post(fb_url, data=payload)
    if res.status_code == 200:
        print(f"✅ Publication réussie sur Facebook : {video['title']}")
        return True
    else:
        print(f"❌ Erreur publication Facebook: {res.status_code} - {res.text}")
        return False

def main():
    print("🚀 [AutoYou2Face] Démarrage de la publication en boucle...")
    
    if not all([YOUTUBE_API_KEY, YOUTUBE_CHANNEL_ID, META_ACCESS_TOKEN, FB_PAGE_ID]):
        print("❌ Configuration incomplète. Vérifiez vos GitHub Secrets.")
        exit(1)

    all_videos = get_channel_videos()
    if not all_videos:
        print("⚠️ Aucune vidéo disponible trouvée sur la chaîne YouTube.")
        return

    history = load_history()
    
    # Filtrer les vidéos non encore publiées dans ce cycle
    unposted_videos = [v for v in all_videos if v["id"] not in history]

    # Si toutes les vidéos ont déjà été publiées, on réinitialise le cycle !
    if not unposted_videos:
        print("🔄 Cycle terminé ! Toutes les vidéos ont été publiées. Réinitialisation du cycle...")
        history = []
        unposted_videos = all_videos

    # Choix aléatoire d'une vidéo parmi les non publiées
    selected_video = random.choice(unposted_videos)
    print(f"🎯 Vidéo sélectionnée au hasard : {selected_video['title']} (ID: {selected_video['id']})")

    if post_to_facebook(selected_video):
        history.append(selected_video["id"])
        save_history(history)

if __name__ == "__main__":
    main()

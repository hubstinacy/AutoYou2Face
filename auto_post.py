import os
import sys
import json
import requests

# =====================================================================
# AutoYou2Face - Main Script
# Copyright (c) 2026 Hubstinacy / Grégory Hubin (aka The Nasty Mariol)
# All Rights Reserved.
# =====================================================================

def load_credentials():
    """
    Charge les identifiants de manière sécurisée :
    1. Depuis les variables d'environnement (GitHub Secrets / OS)
    2. Depuis un fichier local 'config.txt' si disponible
    """
    credentials = {
        "YOUTUBE_API_KEY": os.environ.get("YOUTUBE_API_KEY"),
        "YOUTUBE_CHANNEL_ID": os.environ.get("YOUTUBE_CHANNEL_ID"),
        "META_ACCESS_TOKEN": os.environ.get("META_ACCESS_TOKEN"),
        "FB_PAGE_ID": os.environ.get("FB_PAGE_ID")
    }

    # Si une clé manque, tentative de lecture du fichier config.txt local
    if not all(credentials.values()) and os.path.exists("config.txt"):
        with open("config.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip()
                    if key in credentials and not credentials[key]:
                        credentials[key] = val

    # Vérification des clés manquantes
    missing_keys = [k for k, v in credentials.items() if not v]
    
    if missing_keys:
        print(f"❌ Configuration incomplète. Clés manquantes : {', '.join(missing_keys)}")
        print("💡 Renseignez vos GitHub Secrets ou votre fichier config.txt.")
        sys.exit(1)

    return credentials


def load_posted_history(filename="posted_videos.json"):
    """Charge l'historique des vidéos déjà publiées sur Facebook."""
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []


def save_posted_history(history, filename="posted_videos.json"):
    """Enregistre la liste mise à jour des vidéos publiées."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)


def get_latest_youtube_video(api_key, channel_id):
    """Récupère les détails de la dernière vidéo publiée sur la chaîne YouTube."""
    url = f"https://www.googleapis.com/youtube/v3/search?key={api_key}&channelId={channel_id}&part=snippet,id&order=date&maxResults=1"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"❌ Erreur API YouTube ({response.status_code}): {response.text}")
        return None

    data = response.json()
    items = data.get("items", [])
    
    if not items:
        print("ℹ️ Aucune vidéo trouvée sur cette chaîne YouTube.")
        return None

    latest = items[0]
    video_id = latest.get("id", {}).get("videoId")
    
    if not video_id:
        return None  # Peut être une playlist ou une chaîne

    title = latest["snippet"]["title"]
    description = latest["snippet"]["description"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    return {
        "id": video_id,
        "title": title,
        "description": description,
        "url": video_url
    }


def post_to_facebook(access_token, page_id, message, link):
    """Publie un message avec lien vers la Page Facebook via Meta Graph API."""
    url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
    payload = {
        "message": message,
        "link": link,
        "access_token": access_token
    }
    
    response = requests.post(url, data=payload)
    
    if response.status_code == 200:
        print(f"✅ Publication réussie sur Facebook (Post ID: {response.json().get('id')})")
        return True
    else:
        print(f"❌ Erreur API Facebook ({response.status_code}): {response.text}")
        return False


def main():
    print("🚀 [AutoYou2Face] Démarrage de l'application...")
    print("Developed by Grégory Hubin (The Nasty Mariol) / Hubstinacy\n")

    # 1. Chargement des identifiants
    config = load_credentials()

    # 2. Chargement de l'historique
    posted_history = load_posted_history()

    # 3. Récupération de la dernière vidéo YouTube
    latest_video = get_latest_youtube_video(
        config["YOUTUBE_API_KEY"],
        config["YOUTUBE_CHANNEL_ID"]
    )

    if not latest_video:
        print("▶️ Aucune nouvelle vidéo à traiter.")
        return

    video_id = latest_video["id"]

    # 4. Vérification du doublon
    if video_id in posted_history:
        print(f"ℹ️ La vidéo '{latest_video['title']}' (ID: {video_id}) a déjà été publiée.")
        return

    # 5. Publication sur Facebook
    print(f"📌 Nouvelle vidéo détectée : {latest_video['title']}")
    message = f"🎵 {latest_video['title']}\n\n{latest_video['description']}"
    
    success = post_to_facebook(
        config["META_ACCESS_TOKEN"],
        config["FB_PAGE_ID"],
        message,
        latest_video["url"]
    )

    # 6. Sauvegarde dans l'historique si publication réussie
    if success:
        posted_history.append(video_id)
        save_posted_history(posted_history)
        print("💾 Historique mis à jour.")


if __name__ == "__main__":
    main()

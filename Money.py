import os
import time
import openai
import schedule
from moviepy.editor import TextClip, CompositeVideoClip
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configuration OpenAI
openai.api_key = "VOTRE_CLE_API_OPENAI"

# Scopes nécessaires pour l'API YouTube
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def authenticate_youtube():
    """Authentifie l'utilisateur et retourne le service YouTube."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)

def generate_content():
    """Génère un titre, une description et des tags avec OpenAI."""
    prompt = "Génère un titre, une description et des tags pour un YouTube Short sur un sujet aléatoire."
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.7,
    )
    content = response.choices[0].text.strip().split("\n")
    title = content[0].replace("Titre: ", "")
    description = content[1].replace("Description: ", "")
    tags = content[2].replace("Tags: ", "").split(", ")
    return title, description, tags

def create_video(title, output_path="output.mp4"):
    """Crée une vidéo YouTube Short avec MoviePy."""
    clip = TextClip(title, fontsize=50, color="white", size=(1080, 1920), bg_color="black")
    video = CompositeVideoClip([clip.set_duration(10)])  # Vidéo de 10 secondes
    video.write_videofile(output_path, fps=24)

def upload_short(service, file_path, title, description, tags, category_id="22"):
    """Télécharge une vidéo YouTube Short."""
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": "public",  # "private", "unlisted", or "public"
        },
    }
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = service.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    response = None
    while response is None:
        status, response = request.next_chunk()
        if "id" in response:
            print(f"Vidéo publiée ! ID : {response['id']}")
        else:
            print("Échec de la publication.")

def daily_upload():
    """Génère et publie une vidéo toutes les 24 heures."""
    youtube = authenticate_youtube()
    title, description, tags = generate_content()
    create_video(title)
    upload_short(youtube, "output.mp4", title, description, tags)
    print(f"Vidéo publiée : {title}")

# Planifier la publication toutes les 24 heures
schedule.every().day.at("12:00").do(daily_upload)  # Changez l'heure si nécessaire

if __name__ == "__main__":
    print("Démarrage du programme de publication automatique...")
    while True:
        schedule.run_pending()
        time.sleep(1)

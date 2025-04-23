import re
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from googletrans import Translator
from yt_dlp import YoutubeDL

def get_video_title_fallback(video_url):
    try:
        with YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return info.get('title', None)
    except Exception as e:
        print(f"Erro com yt_dlp ao obter o título: {e}")
        return None

def clean_youtube_url(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    if match:
        video_id = match.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    if match:
        return match.group(1)
    print("❌ Não foi possível extrair o ID do vídeo.")
    return None

def get_video_title(video_url):
    try:
        video_id = extract_video_id(video_url)
        if not video_id:
            raise ValueError("ID do vídeo não pôde ser extraído.")
        clean_url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"[DEBUG] URL formatada para pytube: {clean_url}")
        yt = YouTube(clean_url)
        return yt.title
    except Exception as e:
        print(f"Erro ao obter o título do vídeo: {e}")
        return None

def get_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        english_text = None
        portuguese_text = None
        translated_title = None

        try:
            english_transcript = transcript_list.find_transcript(['en'])
            english_fetched = english_transcript.fetch()
            english_text = " ".join([entry.text for entry in english_fetched])
        except NoTranscriptFound:
            english_text = None

        try:
            portuguese_transcript = transcript_list.find_transcript(['pt', 'pt-BR'])
            portuguese_fetched = portuguese_transcript.fetch()
            portuguese_text = " ".join([entry.text for entry in portuguese_fetched])
        except NoTranscriptFound:
            portuguese_text = None

        if english_text and not portuguese_text:
            try:
                translator = Translator()
                translated = translator.translate(english_text, src='en', dest='pt')
                portuguese_text = translated.text
            except Exception as e:
                raise Exception(f"Erro ao traduzir: {e}")

        if not english_text and not portuguese_text:
            raise Exception("Nenhuma transcrição encontrada em inglês ou português.")

        # Traduzir título junto com a transcrição, se necessário
        if english_text and not portuguese_text:
            try:
                translator = Translator()
                translated_title_obj = translator.translate(get_video_title(f"https://www.youtube.com/watch?v={video_id}"), src='en', dest='pt')
                translated_title = translated_title_obj.text
            except Exception as e:
                print(f"Erro ao traduzir o título: {e}")

        return {
            'english': english_text,
            'portuguese': portuguese_text,
            'translated_title': translated_title
        }

    except TranscriptsDisabled:
        raise Exception("⚠️ As transcrições estão desativadas para este vídeo.")
    except NoTranscriptFound:
        raise Exception("❌ Nenhuma transcrição foi encontrada.")
    except Exception as e:
        raise Exception(f"🚨 Erro ao obter transcrição: {e}")

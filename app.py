import os
import requests
import io
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from pydub import AudioSegment

BOT_TOKEN = os.environ["BOT_TOKEN"]
HF_TOKEN = os.environ["HF_TOKEN"]

def transcribe_with_whisper(audio_bytes):
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "audio/wav"
    }
    # Конвертируем в WAV (Whisper требует WAV)
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="ogg")
    wav_io = io.BytesIO()
    audio.export(wav_io, format="wav")
    wav_data = wav_io.getvalue()

    response = requests.post(
        "https://api-inference.huggingface.co/models/openai/whisper-large-v3",
        headers=headers,
        data=wav_data
    )
    try:
        return response.json().get("text", "").strip()
    except:
        return ""

def generate_response(text):
    if not text:
        return "Не удалось распознать речь. Попробуй ещё раз."
    
    payload = {
        "inputs": f"Пользователь сказал: '{text}'. Ответь как добрый психолог, кратко и с заботой.",
        "parameters": {"max_new_tokens": 100}
    }
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://api-inference.huggingface.co/models/google/flan-t5-small",
        headers=headers,
        json=payload
    )
    try:
        return response.json()[0]["generated_text"].strip()
    except:
        return "Спасибо, что поделился. Ты не один — я рядом. 💙"

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        voice = await update.message.voice.get_file()
        voice_bytes = await voice.download_as_bytearray()

        # Распознавание
        user_text = transcribe_with_whisper(voice_bytes)
        reply = generate_response(user_text)

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text("Ошибка. Попробуй позже.")
        print("Error:", e)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.run_polling()

if __name__ == "__main__":
    main()

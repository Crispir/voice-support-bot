import os
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# === Настройки из переменных окружения ===
BOT_TOKEN = os.environ["BOT_TOKEN"]
YANDEX_API_KEY = os.environ["YANDEX_API_KEY"]
FOLDER_ID = os.environ["FOLDER_ID"]

# === Распознавание речи (Yandex SpeechKit) ===
def transcribe_voice(voice_bytes):
    headers = {"Authorization": f"Api-Key {YANDEX_API_KEY}"}
    params = {
        "folderId": FOLDER_ID,
        "lang": "ru-RU",
        "format": "oggopus",
        "sampleRateHertz": 48000,
    }
    response = requests.post(
        "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize",
        headers=headers,
        params=params,
        data=voice_bytes
    )
    result = response.json()
    return result.get("result", "").strip()

# === Генерация ответа через Yandex GPT ===
def generate_response(user_text):
    prompt = (
        "Ты — добрый, мудрый и поддерживающий психолог. "
        "Пользователь сказал: «{user_text}». "
        "Ответь кратко (1–2 предложения), с эмпатией, мягко и без советов, если не просят. "
        "Иногда задавай лёгкий уточняющий вопрос или напоминай о дыхании, заботе о себе. "
        "Не используй маркдаун, только чистый текст."
    ).format(user_text=user_text)

    body = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {"stream": False, "temperature": 0.6, "maxTokens": 150},
        "messages": [{"role": "user", "text": prompt}]
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {YANDEX_API_KEY}"
    }

    response = requests.post(
        "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
        json=body,
        headers=headers
    )

    try:
        answer = response.json()["result"]["alternatives"][0]["message"]["text"]
        return answer
    except:
        return "Спасибо, что поделился. Ты не один — я рядом. 💙"

# === Обработка голосового сообщения ===
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Скачиваем голосовое
        voice_file = await update.message.voice.get_file()
        voice_bytes = await voice_file.download_as_bytearray()

        # Распознаём
        user_text = transcribe_voice(voice_bytes)
        if not user_text:
            await update.message.reply_text("Не удалось распознать речь. Попробуй говорить чётче.")
            return

        # Генерируем ответ
        ai_reply = generate_response(user_text)

        # Отправляем
        await update.message.reply_text(ai_reply)

    except Exception as e:
        await update.message.reply_text("Произошла ошибка. Попробуй позже.")
        print("Ошибка:", e)

# === Запуск бота ===
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.run_polling()

if __name__ == "__main__":
    main()

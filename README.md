# Yordamchi Bot (MrYordam)

Navbatlarni boshqarish uchun mo'ljallangan Telegram bot. Ushbu bot tadbirkorlarga mijozlar navbatini avtomatlashtirishda yordam beradi.

## Imkoniyatlar:
- 👥 Mijozlarni navbatga qo'shish
- 📊 Mijozlar tarixini ko'rish (1, 2, 3 oylik va barcha vaqtlar)
- 📝 Xabar matnini shaxsiylashtirish
- 🏪 Do'kon nomi va telefonini sozlash
- 🤖 Userbot (Shaxsiy akkauntdan xabar yuborish) orqali ishlash

## O'rnatish va ishga tushirish:

1. **Repozitoriyani yuklab oling:**
   ```bash
   git clone https://github.com/Husanboy777zz/MrYordam_Bot.git
   cd MrYordam_Bot
   ```

2. **Virtual muhitni yarating va kutubxonalarni o'rnating:**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **.env faylini yarating:**
   Loyiha papkasida `.env` faylini yarating va quyidagi ma'lumotlarni to'ldiring:
   ```env
   BOT_TOKEN=sizning_bot_tokeningiz
   API_ID=sizning_telegram_api_id
   API_HASH=sizning_telegram_api_hash
   ESKIZ_EMAIL=sizning_emailingiz
   ESKIZ_PASSWORD=sizning_parolingiz
   ```

4. **Userbotga kiring:**
   ```bash
   python login_userbot.py
   ```

5. **Botni ishga tushiring:**
   ```bash
   python run.py
   ```

## Texnologiyalar:
- Python 3.10+
- python-telegram-bot
- Pyrogram (Userbot)
- SQLite (Ma'lumotlar bazasi)
- APScheduler (Vaqtni boshqarish)

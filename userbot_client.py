import asyncio
import logging
import os
from pyrogram import Client
from dotenv import load_dotenv

load_dotenv()

API_ID_RAW = os.getenv("API_ID")
try:
    API_ID = int(API_ID_RAW) if API_ID_RAW else None
except ValueError:
    API_ID = None

API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# Userbot ob'ekti
# Agar SESSION_STRING bo'lsa, undan foydalanamiz, aks holda fayldan
if SESSION_STRING:
    app_ub = Client("my_account", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
else:
    app_ub = Client("my_account", api_id=API_ID, api_hash=API_HASH)

logger = logging.getLogger(__name__)

async def send_userbot_msg(phone: str, message: str) -> bool:
    """Mijozga shaxsiy akkaunt nomidan Telegram xabar yuborish."""
    if not API_ID or not API_HASH:
        logger.warning("API_ID yoki API_HASH sozlanmagan!")
        return False
        
    # Telefon raqamni tozalash
    phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    if not phone.startswith("998"):
        phone = "998" + phone if len(phone) == 9 else phone
    
    # Pyrogram xalqaro format uchun + belgisi bilan ishlashi tavsiya etiladi
    full_phone = "+" + phone

    try:
        if not app_ub.is_connected:
            logger.info("Userbot ulanmagan, ulanishga urinish...")
            try:
                # 30 soniya kutamiz, agar ulanmasa timeout beradi
                await asyncio.wait_for(app_ub.start(), timeout=30)
            except asyncio.TimeoutError:
                logger.error("Userbot ulanishda vaqt tugadi (Timeout).")
                return False
            except Exception as e:
                logger.error(f"Userbotni ishga tushirib bo'lmadi: {e}")
                return False
            
        # PeerIdInvalid xatosini oldini olish uchun raqamni kontaktga qo'shishga urinish
        from pyrogram import types, errors
        
        try:
            # Avval to'g'ridan-to'g'ri yuborib ko'ramiz
            logger.info(f"Userbot xabar yubormoqda: {full_phone}")
            await app_ub.send_message(full_phone, message)
        except (errors.PeerIdInvalid, errors.InviteHashExpired):
            logger.info(f"Raqam tanilmadi, kontaktga qo'shilmoqda: {full_phone}")
            # Agar tanimasa, kontaktga qo'shib keyin yuboramiz
            contact = types.InputPhoneContact(phone=full_phone, first_name=phone)
            await app_ub.import_contacts([contact])
            await app_ub.send_message(full_phone, message)
            
        logger.info(f"Userbot orqali xabar muvaffaqiyatli ketdi: {full_phone}")
        return True
    except Exception as e:
        logger.error(f"Userbot xatoligi ({full_phone}): {type(e).__name__}: {e}")
        return False

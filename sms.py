import requests
import logging
import os

logger = logging.getLogger(__name__)

ESKIZ_EMAIL    = os.getenv("ESKIZ_EMAIL", "")
ESKIZ_PASSWORD = os.getenv("ESKIZ_PASSWORD", "")
ESKIZ_BASE_URL = "https://notify.eskiz.uz/api"
ESKIZ_FROM     = os.getenv("ESKIZ_FROM", "4546")  # Eskiz da ro'yxatdan o'tgan sender nomi


def _get_token() -> str | None:
    """Eskiz.uz dan JWT token olish."""
    if not ESKIZ_EMAIL or "sizning@email.com" in ESKIZ_EMAIL or not ESKIZ_PASSWORD or "parolingiz" in ESKIZ_PASSWORD:
        logger.warning("Eskiz credentials not configured. Skipping SMS.")
        return None
    try:
        resp = requests.post(
            f"{ESKIZ_BASE_URL}/auth/login",
            data={"email": ESKIZ_EMAIL, "password": ESKIZ_PASSWORD},
            timeout=10,
        )
        data = resp.json()
        return data.get("data", {}).get("token")
    except Exception as e:
        logger.error(f"Eskiz token error: {e}")
        return None


def _normalize_phone(phone: str) -> str:
    """Raqamni tozalash va 998XXXXXXXXX formatga keltirish."""
    phone = phone.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if phone.startswith("998") and len(phone) == 12:
        return phone
    if phone.startswith("9") and len(phone) == 9:
        return "998" + phone
    return phone


def send_sms(phone: str, message: str) -> bool:
    """SMS yuborish. True qaytarsa muvaffaqiyatli."""
    phone = _normalize_phone(phone)
    logger.info(f"Sending SMS to {phone}: {message}")

    token = _get_token()
    if not token:
        logger.error("Could not obtain Eskiz token. Check ESKIZ_EMAIL and ESKIZ_PASSWORD.")
        return False

    try:
        resp = requests.post(
            f"{ESKIZ_BASE_URL}/message/sms/send",
            data={
                "mobile_phone": phone,
                "message": message,
                "from": ESKIZ_FROM,
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        data = resp.json()
        logger.info(f"Eskiz response: {data}")
        status = data.get("status") or ""
        return status in ("waiting", "success")
    except Exception as e:
        logger.error(f"SMS send error: {e}")
        return False

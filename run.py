import os
import subprocess
import sys
import venv
from pathlib import Path

# Sozlamalar
VENV_DIR = Path("venv")
REQUIREMENTS_FILE = Path("requirements.txt")
BOT_SCRIPT = Path("bot.py")
ENV_FILE = Path(".env")

def print_status(msg):
    print(f"\n[+] {msg}")

def check_venv():
    if not VENV_DIR.exists():
        print_status("Virtual muhit (venv) topilmadi. Yaratilmoqda...")
        venv.create(VENV_DIR, with_pip=True)
        print_status("Venv muvaffaqiyatli yaratildi.")
    else:
        print_status("Virtual muhit mavjud.")

def get_venv_python():
    if os.name == "nt":  # Windows
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"

def install_requirements():
    python_exe = get_venv_python()
    print_status("Kutubxonalar tekshirilmoqda va o'rnatilmoqda...")
    try:
        subprocess.check_call([str(python_exe), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])
        print_status("Barcha kutubxonalar tayyor.")
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Xatolik: Kutubxonalarni o'rnatib bo'lmadi: {e}")
        sys.exit(1)

def check_env():
    if not ENV_FILE.exists():
        print(f"\n[!] Xatolik: {ENV_FILE} fayli topilmadi!")
        print("Iltimos, .env faylini yarating va tokenlarni kiriting.")
        sys.exit(1)
    
    with open(ENV_FILE, "r") as f:
        content = f.read()
        if "1234567890:AAxxxxxxxx" in content or "sizning@email.com" in content:
            print("\n[!] DIQQAT: .env faylida hali ham namunaviy (placeholders) ma'lumotlar turibdi!")
            print("Iltimos, haqiqiy BOT_TOKEN va Eskiz ma'lumotlarini kiriting.")
            # Biz baribir davom etishimiz mumkin, lekin bot xato beradi
    print_status(".env fayli tekshirildi.")

def run_bot():
    python_exe = get_venv_python()
    print_status("Bot ishga tushirilmoqda...\n" + "="*30)
    try:
        # Botni ishga tushiramiz
        subprocess.run([str(python_exe), str(BOT_SCRIPT)])
    except KeyboardInterrupt:
        print("\n\n[!] Bot to'xtatildi.")
    except Exception as e:
        print(f"\n[!] Botni ishga tushirishda xatolik: {e}")

if __name__ == "__main__":
    print("=== Yordamchi Bot Avtomatik Ishga Tushirgich ===\n")
    
    check_venv()
    install_requirements()
    check_env()
    run_bot()

import asyncio
import os
from pyrogram import Client
from dotenv import load_dotenv

load_dotenv()

async def main():
    api_id_raw = os.getenv("API_ID")
    api_id = int(api_id_raw) if api_id_raw else None
    api_hash = os.getenv("API_HASH")
    
    if not api_id or not api_hash:
        print("Xatolik: .env faylida API_ID va API_HASH kiritilmagan!")
        return

    async with Client("my_account", api_id=api_id, api_hash=api_hash) as app:
        session_string = await app.export_session_string()
        print("\n" + "="*50)
        print("SIZNING SESSION STRING (MATNLI SESSIYA):")
        print("="*50 + "\n")
        print(session_string)
        print("\n" + "="*50)
        print("Ushbu kodni nusxalab oling va Render-ga SESSION_STRING nomi bilan qo'shing.")

if __name__ == "__main__":
    asyncio.run(main())

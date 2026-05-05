import asyncio
from userbot_client import app_ub

async def main():
    print("=== Userbot Login ===")
    print("Hozir sizdan telefon raqamingiz va Telegram'dan kelgan kod so'raladi.")
    async with app_ub:
        me = await app_ub.get_me()
        print(f"\n✅ Muvaffaqiyatli kirdingiz!")
        print(f"Akkaunt: {me.first_name} (@{me.username if me.username else 'username yoq'})")
        print("Endi botni ishga tushirsangiz bo'ladi.")

if __name__ == "__main__":
    asyncio.run(main())

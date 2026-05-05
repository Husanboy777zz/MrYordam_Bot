import asyncio
from userbot_client import app_ub

async def check_status():
    print("Userbot holatini tekshirilmoqda...")
    try:
        await app_ub.start()
        me = await app_ub.get_me()
        print(f"✅ Userbot faol: {me.first_name} (@{me.username})")
        await app_ub.stop()
    except Exception as e:
        print(f"❌ Userbotda muammo: {e}")

if __name__ == "__main__":
    asyncio.run(check_status())

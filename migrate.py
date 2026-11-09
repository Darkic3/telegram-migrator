import asyncio
import sys
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telethon.errors import FloodWaitError, ChatWriteForbiddenError
from config import API_ID, API_HASH, TARGET_CHANNEL, SESSION_NAME


async def forward_media():
    """تابع اصلی برای انتقال عکس‌ها و فیلم‌ها"""
    
    # اتصال به تلگرام
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    await client.start()
    me = await client.get_me()
    print(f"✅ وارد شدی به عنوان: {me.first_name} (@{me.username})")
    
    try:
        # دریافت اطلاعات کانال مقصد
        channel = await client.get_entity(TARGET_CHANNEL)
        print(f"📤 کانال مقصد: {channel.title}")
    except Exception as e:
        print(f"❌ خطا در دریافت کانال مقصد: {e}")
        await client.disconnect()
        return
    
    # شمارنده‌ها
    total_forwarded = 0
    total_skipped = 0
    batch = []
    batch_size = 30  # تعداد پیام در هر دسته
    
    print("\n🔍 شروع بررسی Saved Messages...")
    print("⏳ این کار ممکنه بسته به تعداد پیام‌ها زمان‌بر باشه...\n")
    
    try:
        async for message in client.iter_messages(me):
            # بررسی اینکه پیام حاوی مدیا هست یا نه
            if not message.media:
                total_skipped += 1
                continue
            
            # فیلتر: فقط عکس و فیلم
            is_photo = isinstance(message.media, MessageMediaPhoto)
            is_video = (
                isinstance(message.media, MessageMediaDocument) and
                message.media.document and
                any(attr.__class__.__name__ == 'DocumentAttributeVideo' 
                    for attr in message.media.document.attributes)
            )
            
            if not (is_photo or is_video):
                total_skipped += 1
                continue
            
            # اضافه کردن به دسته
            batch.append(message.id)
            
            # ارسال دسته وقتی پر شد
            if len(batch) >= batch_size:
                try:
                    await client.forward_messages(channel, batch, me)
                    total_forwarded += len(batch)
                    print(f"✅ {total_forwarded} پیام منتقل شد | رد شده: {total_skipped}")
                    batch = []
                    await asyncio.sleep(3)  # جلوگیری از Flood Wait
                except FloodWaitError as e:
                    print(f"⏸️ تلگرام درخواست استراحت کرد: {e.seconds} ثانیه صبر می‌کنم...")
                    await asyncio.sleep(e.seconds + 5)
                    # دوباره تلاش برای ارسال همین دسته
                    await client.forward_messages(channel, batch, me)
                    total_forwarded += len(batch)
                    batch = []
                except ChatWriteForbiddenError:
                    print("❌ دسترسی نوشتن در کانال نداری! مطمئن شو ادمین هستی.")
                    break
        
        # ارسال پیام‌های باقیمانده
        if batch:
            try:
                await client.forward_messages(channel, batch, me)
                total_forwarded += len(batch)
            except FloodWaitError as e:
                print(f"⏸️ صبر برای {e.seconds} ثانیه...")
                await asyncio.sleep(e.seconds + 5)
                await client.forward_messages(channel, batch, me)
                total_forwarded += len(batch)
        
        print("\n" + "="*50)
        print(f"🎉 عملیات تمام شد!")
        print(f"📊 کل منتقل شده: {total_forwarded}")
        print(f"🚫 کل رد شده (بدون مدیا): {total_skipped}")
        print("="*50)
        
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
    
    await client.disconnect()
    print("\n👋 اتصال قطع شد.")


if __name__ == "__main__":
    # اجرای تابع اصلی
    if sys.platform == 'win32':
        # برای ویندوز نیاز به این تنظیمات هستیم
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(forward_media())
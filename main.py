import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters, CallbackQueryHandler, MessageHandler
import urllib3
import asyncio
import logging
from telegram.constants import ChatMemberStatus
import pytz  # Yeni import
import telegram
import time
from PIL import Image
import io
import re
import json
from pathlib import Path
import psutil
import signal
from admin_utils import UserManager, UserCredits

# Zaman dilimi ayarı
os.environ['TZ'] = 'UTC'  # UTC zaman dilimini ayarla

# HTTPS uyarılarını devre dışı bırak
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Logger ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram bot token ve kanal adı
TOKEN = '7694637533:AAEz00Fc4lnLYqByt_56Bxr5YQqyPAlgosA'
CHANNEL_USERNAME = '@clonicai'

# Yeni komutlar için sabitler
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
THUMB_SIZE = (320, 320)

# Kullanıcı ayarları için sabitler
USER_DATA_DIR = Path("user_data")
USER_DATA_DIR.mkdir(exist_ok=True)

# Chat geçmişi için yeni sınıf ve sabitler
CHAT_HISTORY_DIR = Path("chat_history")
CHAT_HISTORY_DIR.mkdir(exist_ok=True)
MAX_HISTORY_AGE = 24 * 60 * 60  # 24 saat (saniye cinsinden)
MAX_HISTORY_LENGTH = 10  # Maksimum kaç mesajı hatırlasın

# Global değişkenler
user_manager = UserManager()

# Kredi kontrolü decorator'ı
def require_credits(feature: str):
    def decorator(func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            
            # Premium kullanıcılar için kredi kontrolü yapma
            if user_manager.is_premium(user_id):
                return await func(update, context, *args, **kwargs)
            
            # Yasaklı kullanıcıları kontrol et
            if user_manager.is_banned(user_id):
                await update.message.reply_text(
                    "🚫 Hesabınız yasaklanmış durumda!\n"
                    "Destek için: @Cepyseo"
                )
                return
            
            # Kredi kontrolü
            credits = UserCredits(user_id)
            if not credits.check_credits(feature):
                remaining = credits.get_credits()
                await update.message.reply_text(
                    f"❌ Günlük kullanım limitiniz doldu!\n\n"
                    f"🔄 Limitler her gün sıfırlanır.\n"
                    f"👑 Premium üyelik için: @Cepyseo\n\n"
                    f"📊 Kalan Kredileriniz:\n"
                    f"🤖 AI Sohbet: {remaining['ai_chat']}\n"
                    f"🖼️ Görsel Arama: {remaining['image_search']}\n"
                    f"📁 Dosya İşlemleri: {remaining['file_operations']}"
                )
                return
            
            # Krediyi kullan
            credits.use_credit(feature)
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

class ChatHistory:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.history_file = CHAT_HISTORY_DIR / f"{user_id}.json"
        self.messages = self._load_history()

    def _load_history(self) -> list:
        """Kullanıcının sohbet geçmişini yükle"""
        if self.history_file.exists():
            try:
                history = json.loads(self.history_file.read_text())
                # 24 saatten eski mesajları temizle
                current_time = time.time()
                history = [
                    msg for msg in history
                    if current_time - msg.get('timestamp', 0) < MAX_HISTORY_AGE
                ]
                return history[-MAX_HISTORY_LENGTH:] if history else []
            except Exception as e:
                logger.error(f"Sohbet geçmişi yükleme hatası: {e}")
        return []

    def add_message(self, role: str, content: str):
        """Yeni mesaj ekle"""
        self.messages.append({
            'role': role,
            'content': content,
            'timestamp': time.time()
        })
        # Maksimum mesaj sayısını koru
        if len(self.messages) > MAX_HISTORY_LENGTH:
            self.messages = self.messages[-MAX_HISTORY_LENGTH:]
        self._save_history()

    def _save_history(self):
        """Sohbet geçmişini kaydet"""
        try:
            self.history_file.write_text(json.dumps(self.messages, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Sohbet geçmişi kaydetme hatası: {e}")

    def get_context(self) -> str:
        """Sohbet bağlamını oluştur"""
        if not self.messages:
            return ""
        
        context = "Önceki konuşmalarımız:\n\n"
        for msg in self.messages:
            role = "Sen" if msg['role'] == 'user' else "Ben"
            context += f"{role}: {msg['content']}\n"
        return context

    def clear(self):
        """Sohbet geçmişini temizle"""
        self.messages = []
        if self.history_file.exists():
            self.history_file.unlink()

# Kullanıcı ayarlarını yöneten fonksiyonlar
def get_user_data(user_id: int) -> dict:
    """Kullanıcı verilerini getir"""
    user_file = USER_DATA_DIR / f"{user_id}.json"
    if user_file.exists():
        return json.loads(user_file.read_text())
    return {"default_thumb": None}

def save_user_data(user_id: int, data: dict):
    """Kullanıcı verilerini kaydet"""
    user_file = USER_DATA_DIR / f"{user_id}.json"
    user_file.write_text(json.dumps(data))

# Hoş Geldin Mesajı
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Kullanıcı bilgilerini al
    user = update.effective_user
    first_name = user.first_name if user.first_name else "Değerli Kullanıcı"

    welcome_message = (
        f"🎉 *Merhaba {first_name}!*\n\n"
        "Ben *ClonicAI Bot*, yapay zeka destekli çok yönlü bir asistanım. "
        "Size aşağıdaki konularda yardımcı olabilirim:\n\n"
        "🤖 *AI Sohbet*\n"
        "• Yapay zeka ile sohbet edebilir\n"
        "• Sorularınıza detaylı yanıtlar alabilir\n"
        "• 24 saat sohbet geçmişi tutabilirsiniz\n\n"
        "🖼️ *Görsel İşlemler*\n"
        "• Yüksek kaliteli görseller arayabilir\n"
        "• Dosyalarınıza küçük resim ekleyebilir\n"
        "• Dosya adlarını düzenleyebilirsiniz\n\n"
        "📱 *Kolay Kullanım*\n"
        "• Türkçe dil desteği\n"
        "• Hızlı yanıt süresi\n"
        "• Kullanıcı dostu arayüz\n\n"
        "Aşağıdaki butonları kullanarak daha fazla bilgi alabilirsiniz:"
    )

    # Inline butonları oluştur
    keyboard = [
        [
            InlineKeyboardButton("📚 Komutlar", callback_data="commands"),
            InlineKeyboardButton("ℹ️ Yardım", callback_data="help")
        ],
        [
            InlineKeyboardButton("📢 Kanal", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"),
            InlineKeyboardButton("👨‍💻 Geliştirici", url="https://t.me/clonicai")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=welcome_message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# Callback sorgularını işle
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Kullanıcıya geri bildirim gönder

    # Admin işlemleri
    if query.data.startswith("admin_"):
        if not user_manager.is_admin(query.from_user.username):
            await query.edit_message_text("⛔️ Bu işlemi yapma yetkiniz yok!")
            return

        if query.data == "admin_broadcast":
            context.user_data['admin_state'] = 'waiting_broadcast'
            await query.edit_message_text(
                "📢 *Duyuru Mesajını Girin*\n\n"
                "İptal etmek için /cancel yazın.",
                parse_mode='Markdown'
            )

        elif query.data == "admin_premium":
            context.user_data['admin_state'] = 'waiting_premium_user'
            await query.edit_message_text(
                "👑 *Premium Üyelik*\n\n"
                "Kullanıcı ID veya kullanıcı adını girin.\n"
                "İptal etmek için /cancel yazın.",
                parse_mode='Markdown'
            )

        elif query.data == "admin_ban":
            context.user_data['admin_state'] = 'waiting_ban_user'
            await query.edit_message_text(
                "🚫 *Kullanıcı Yasakla*\n\n"
                "Yasaklanacak kullanıcının ID veya kullanıcı adını girin.\n"
                "İptal etmek için /cancel yazın.",
                parse_mode='Markdown'
            )

        elif query.data == "admin_unban":
            context.user_data['admin_state'] = 'waiting_unban_user'
            await query.edit_message_text(
                "✅ *Yasak Kaldır*\n\n"
                "Yasağı kaldırılacak kullanıcının ID veya kullanıcı adını girin.\n"
                "İptal etmek için /cancel yazın.",
                parse_mode='Markdown'
            )

        elif query.data == "admin_stats":
            # İstatistikleri göster
            premium_count = len(user_manager.premium_users)
            banned_count = len(user_manager.banned_users)
            
            stats_text = (
                "📊 *Bot İstatistikleri*\n\n"
                f"👑 Premium Kullanıcılar: {premium_count}\n"
                f"🚫 Yasaklı Kullanıcılar: {banned_count}\n"
            )
            
            await query.edit_message_text(
                stats_text,
                parse_mode='Markdown'
            )

    if query.data == "commands":
        commands_text = (
            "*📋 Kullanılabilir Komutlar:*\n\n"
            "🤖 *AI Komutları:*\n"
            "`/ai` - Yapay zeka ile sohbet\n"
            "`/ai_history` - Sohbet geçmişini görüntüle\n"
            "`/ai_clear` - Sohbet geçmişini temizle\n\n"
            "🖼️ *Görsel Komutları:*\n"
            "`/img` - Görsel ara\n"
            "`/thumb` - Küçük resim ekle\n"
            "`/view_thumb` - Küçük resmi görüntüle\n"
            "`/del_thumb` - Küçük resmi sil\n\n"
            "📁 *Dosya Komutları:*\n"
            "`/rename` - Dosya adı değiştir\n\n"
            "ℹ️ *Diğer Komutlar:*\n"
            "`/start` - Botu başlat\n"
            "`/kanal` - Kanal bilgisi"
        )
        await query.edit_message_text(text=commands_text, parse_mode='Markdown')

    elif query.data == "help":
        help_text = (
            "*❓ Nasıl Kullanılır:*\n\n"
            "*1. AI Sohbet:*\n"
            "• `/ai merhaba` yazarak sohbete başlayın\n"
            "• Her türlü sorunuzu sorabilirsiniz\n"
            "• 24 saat boyunca konuşma bağlamını hatırlar\n\n"
            "*2. Görsel Arama:*\n"
            "• `/img kedi` gibi aramalar yapın\n"
            "• Türkçe aramalar desteklenir\n\n"
            "*3. Dosya İşlemleri:*\n"
            "• Dosya gönderin ve yeniden adlandırın\n"
            "• Küçük resim ekleyin veya silin\n\n"
            "*🔔 Önemli Notlar:*\n"
            "• Bot kullanımı için kanala üye olmalısınız\n"
            "• Dosya boyutu 10MB'ı geçmemelidir\n"
            "• Desteklenen formatlar: jpg, jpeg, png, gif\n\n"
            "Sorun yaşarsanız @clonicai ile iletişime geçin."
        )
        await query.edit_message_text(text=help_text, parse_mode='Markdown')

# Görsel Alma Fonksiyonu
@require_credits('image_search')
async def get_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Üyelik kontrolü
    user_id = update.effective_user.id
    is_member = await check_membership(user_id, context.bot, CHANNEL_USERNAME)

    if not is_member:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🔒 Lütfen botu kullanabilmek için {CHANNEL_USERNAME} kanalına katılın.",
            parse_mode='Markdown'
        )
        return

    # Arama terimi kontrolü
    if not context.args:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="ℹ️ Lütfen bir arama terimi girin:\n`/img <arama terimi>`",
            parse_mode='Markdown'
        )
        return

    prompt = " ".join(context.args)
    
    try:
        # Kullanıcıya bekleme mesajı
        wait_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🔍 Görsel aranıyor...",
            parse_mode='Markdown'
        )

        # API isteği
        base_api_url = "https://death-image.ashlynn.workers.dev"
        enhanced_prompt = enhance_prompt(prompt)
        api_url = f"{base_api_url}/?prompt={requests.utils.quote(enhanced_prompt)}&image=1&dimensions=tall&safety=true"

        response = requests.get(
            api_url,
            headers={'User-Agent': 'Mozilla/5.0'},
            verify=False,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        # Bekleme mesajını sil
        await wait_message.delete()
        
        if 'images' in data and len(data['images']) > 0:
            image_url = data['images'][0]
            # Görseli gönder
            caption = f"🎨 Arama terimi: `{prompt}`"
            if prompt != enhanced_prompt:  # Eğer çeviri yapıldıysa
                caption += f"\n🔄 İngilizce çeviri: `{enhanced_prompt}`"
            
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=image_url,
                caption=caption,
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Üzgünüm, görsel bulunamadı. Lütfen farklı bir arama terimi deneyin.",
                parse_mode='Markdown'
            )

    except requests.exceptions.Timeout:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⏰ Zaman aşımı: Sunucu yanıt vermiyor. Lütfen daha sonra tekrar deneyin.",
            parse_mode='Markdown'
        )
    except requests.exceptions.RequestException as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ Bir hata oluştu: {str(e)}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Görsel arama hatası: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin.",
            parse_mode='Markdown'
        )

# Kanal Bilgisi Komutu
async def channel_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_message = (
        f"📢 **Resmi Kanalımız:** {CHANNEL_USERNAME}\n\n"
        "Botu kullanabilmek için kanalımıza katılmanız gerekmektedir.\n"
        "Kanalımıza katılarak en son güncellemelerden, yapay zeka ve teknoloji haberlerinden haberdar olun!"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=channel_message, parse_mode='Markdown')

# Üyelik Kontrol Fonksiyonu
async def check_membership(user_id, bot, channel_username, timeout=10):
    try:
        member = await asyncio.wait_for(bot.get_chat_member(chat_id=channel_username, user_id=user_id), timeout=timeout)
        is_member = member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
        logger.info(f"Kullanıcı {user_id} için üyelik durumu: {is_member}")
        return is_member
    except asyncio.TimeoutError:
        logger.error("Üyelik kontrolü zaman aşımına uğradı.")
        return False
    except Exception as e:
        logger.error(f"Üyelik kontrolü hatası: {e}")
        return False

# Promptu Geliştirme Fonksiyonu
def enhance_prompt(prompt):
    try:
        # Türkçe prompt'u iyileştir
        prompt_mapping = {
            # Renkler
            'kırmızı': 'vibrant red',
            'mavi': 'deep blue',
            'yeşil': 'vivid green',
            'sarı': 'bright yellow',
            'siyah': 'deep black',
            'beyaz': 'pure white',
            'mor': 'purple',
            'turuncu': 'orange',
            'pembe': 'pink',
            
            # Sanat stilleri
            'çizim': 'detailed drawing',
            'resim': 'detailed painting',
            'fotoğraf': 'professional photograph',
            'anime': 'high quality anime art',
            'gerçekçi': 'photorealistic',
            'karikatür': 'cartoon style',
            
            # Kalite belirteçleri
            'yüksek kalite': 'high quality',
            'detaylı': 'highly detailed',
            'profesyonel': 'professional',
            'hd': 'high definition',
            '4k': '4k ultra hd',
            'güzel': 'beautiful',
            
            # Kompozisyon
            'manzara': 'landscape',
            'portre': 'portrait',
            'yakın çekim': 'close-up shot',
            'geniş açı': 'wide angle shot'
        }

        # Türkçe karakterleri kontrol et
        turkce_karakterler = set('çğıöşüÇĞİÖŞÜ')
        if any(harf in turkce_karakterler for harf in prompt) or any(kelime in prompt.lower() for kelime in prompt_mapping.keys()):
            # Önce bilinen kelimeleri değiştir
            lower_prompt = prompt.lower()
            for tr, en in prompt_mapping.items():
                if tr in lower_prompt:
                    lower_prompt = lower_prompt.replace(tr, en)
            
            # Sonra Google Translate ile çevir
            translate_url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": "tr",
                "tl": "en",
                "dt": "t",
                "q": lower_prompt
            }
            
            response = requests.get(translate_url, params=params)
            response.raise_for_status()
            
            result = response.json()
            if result and len(result) > 0 and len(result[0]) > 0:
                translated_prompt = result[0][0][0]
                # Kalite artırıcı eklemeler
                enhanced_prompt = f"{translated_prompt}, high quality, detailed, professional"
                logger.info(f"Geliştirilmiş çeviri: {prompt} -> {enhanced_prompt}")
                return enhanced_prompt
            
    except Exception as e:
        logger.error(f"Çeviri hatası: {e}")
    
    return prompt

# Hata yönetimi için yeni fonksiyon
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    if update and hasattr(update, 'effective_chat'):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Bir hata oluştu. Lütfen daha sonra tekrar deneyin."
        )

# Dosya işlemleri için yeni komutlar
async def rename_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dosyayı yeniden adlandır"""
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("❌ Lütfen yeniden adlandırmak istediğiniz dosyayı yanıtlayın ve yeni adı yazın:\n`/rename yeni_ad.uzanti`", parse_mode='Markdown')
        return

    if not context.args:
        await update.message.reply_text("❌ Lütfen yeni dosya adını belirtin:\n`/rename yeni_ad.uzanti`", parse_mode='Markdown')
        return

    new_name = " ".join(context.args)
    old_file = update.message.reply_to_message.document
    
    try:
        file = await context.bot.get_file(old_file.file_id)
        file_content = await file.download_as_bytearray()
        
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=io.BytesIO(file_content),
            filename=new_name,
            caption=f"✅ Dosya başarıyla yeniden adlandırıldı:\n`{old_file.file_name}` ➡️ `{new_name}`",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Dosya yeniden adlandırılırken hata oluştu: {str(e)}")

async def add_thumbnail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dosyaya küçük resim ekle"""
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("❌ Lütfen küçük resim eklemek istediğiniz dosyayı yanıtlayın ve bir resim gönderin.")
        return

    if not update.message.photo:
        await update.message.reply_text("❌ Lütfen küçük resim olarak kullanılacak bir fotoğraf gönderin.")
        return

    try:
        # Dosyayı al
        doc = update.message.reply_to_message.document
        file = await context.bot.get_file(doc.file_id)
        file_content = await file.download_as_bytearray()

        # Küçük resmi al ve boyutlandır
        photo = update.message.photo[-1]  # En büyük boyuttaki fotoğrafı al
        thumb_file = await context.bot.get_file(photo.file_id)
        thumb_content = await thumb_file.download_as_bytearray()
        
        # Küçük resmi işle
        thumb_image = Image.open(io.BytesIO(thumb_content))
        thumb_image.thumbnail(THUMB_SIZE)
        thumb_buffer = io.BytesIO()
        thumb_image.save(thumb_buffer, format='JPEG')
        thumb_buffer.seek(0)

        # Dosyayı küçük resimle birlikte gönder
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=io.BytesIO(file_content),
            filename=doc.file_name,
            thumbnail=thumb_buffer,
            caption="✅ Dosyaya küçük resim eklendi!",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Küçük resim eklenirken hata oluştu: {str(e)}")

# Varsayılan thumb işlemleri
async def save_default_thumb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gönderilen fotoğrafı varsayılan thumb olarak kaydet"""
    user_id = update.effective_user.id
    
    if not update.message.photo:
        await update.message.reply_text("❌ Lütfen bir fotoğraf gönderin!")
        return

    try:
        # En büyük boyuttaki fotoğrafı al
        photo = update.message.photo[-1]
        thumb_file = await context.bot.get_file(photo.file_id)
        thumb_content = await thumb_file.download_as_bytearray()
        
        # Küçük resmi işle
        thumb_image = Image.open(io.BytesIO(thumb_content))
        thumb_image.thumbnail(THUMB_SIZE)
        thumb_buffer = io.BytesIO()
        thumb_image.save(thumb_buffer, format='JPEG')
        thumb_buffer.seek(0)

        # Kullanıcı verilerini güncelle
        user_data = get_user_data(user_id)
        user_data["default_thumb"] = thumb_content.hex()  # Binary veriyi hex olarak sakla
        save_user_data(user_id, user_data)

        await update.message.reply_text("✅ Varsayılan küçük resim başarıyla kaydedildi!")
    except Exception as e:
        await update.message.reply_text(f"❌ Küçük resim kaydedilirken hata oluştu: {str(e)}")

async def delete_default_thumb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Varsayılan thumb'ı sil"""
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    if user_data.get("default_thumb"):
        user_data["default_thumb"] = None
        save_user_data(user_id, user_data)
        await update.message.reply_text("✅ Varsayılan küçük resim silindi!")
    else:
        await update.message.reply_text("❌ Kayıtlı varsayılan küçük resim bulunamadı!")

# Dosya işleme fonksiyonunu güncelle
@require_credits('file_operations')
async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gönderilen dosyayı otomatik işle"""
    if not update.message.document:
        # Eğer fotoğraf gönderildiyse varsayılan thumb olarak kaydet
        if update.message.photo:
            await save_default_thumb(update, context)
        return

    try:
        doc = update.message.document
        original_name = doc.file_name
        
        # Kullanıcıdan yeni dosya adını iste
        ask_msg = await update.message.reply_text(
            "📝 Lütfen dosya için yeni bir ad girin:\n"
            f"Mevcut ad: `{original_name}`\n\n"
            "💡 Not: Sadece dosya adını yazın, uzantı otomatik eklenecektir.",
            parse_mode='Markdown'
        )
        
        # Kullanıcının cevabını bekle
        context.user_data['waiting_rename'] = {
            'file_id': doc.file_id,
            'original_name': original_name,
            'ask_msg': ask_msg
        }
        return

    except Exception as e:
        await update.message.reply_text(f"❌ Dosya işlenirken hata oluştu: {str(e)}")

async def handle_rename_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcının rename yanıtını işle"""
    if 'waiting_rename' not in context.user_data:
        return

    try:
        # Bekleyen dosya bilgilerini al
        file_data = context.user_data['waiting_rename']
        original_name = file_data['original_name']
        ask_msg = file_data['ask_msg']
        
        # Yeni adı al ve temizle
        new_base_name = update.message.text.strip()
        # Uzantıyı koru
        original_ext = original_name.rsplit('.', 1)[1] if '.' in original_name else ''
        new_name = f"{new_base_name}.{original_ext}".lower()
        
        # İşlem mesajı
        process_msg = await update.message.reply_text(
            "🔄 Dosya işleniyor...\n"
            f"📝 Orijinal ad: `{original_name}`\n"
            f"✨ Yeni ad: `{new_name}`\n\n"
            "⏳ Lütfen bekleyin...",
            parse_mode='Markdown'
        )

        # Dosyayı indir
        file = await context.bot.get_file(file_data['file_id'])
        file_content = await file.download_as_bytearray()

        # Kullanıcının varsayılan thumb'ını kontrol et
        user_id = update.effective_user.id
        user_data = get_user_data(user_id)
        thumb_content = None
        
        if user_data.get("default_thumb"):
            thumb_content = bytes.fromhex(user_data["default_thumb"])

        # İşlem mesajını güncelle
        await process_msg.edit_text(
            "🔄 Dosya işleniyor...\n"
            f"📝 Orijinal ad: `{original_name}`\n"
            f"✨ Yeni ad: `{new_name}`\n"
            "🖼️ Küçük resim ekleniyor...",
            parse_mode='Markdown'
        )

        # Dosyayı gönder
        if thumb_content:
            thumb_image = Image.open(io.BytesIO(thumb_content))
            thumb_buffer = io.BytesIO()
            thumb_image.save(thumb_buffer, format='JPEG')
            thumb_buffer.seek(0)

            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=io.BytesIO(file_content),
                filename=new_name,
                thumbnail=thumb_buffer,
                caption=(
                    "✅ Dosya başarıyla işlendi!\n\n"
                    f"📝 Orijinal ad: `{original_name}`\n"
                    f"✨ Yeni ad: `{new_name}`\n"
                    "🖼️ Küçük resim eklendi"
                ),
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=io.BytesIO(file_content),
                filename=new_name,
                caption=(
                    "✅ Dosya başarıyla işlendi!\n\n"
                    f"📝 Orijinal ad: `{original_name}`\n"
                    f"✨ Yeni ad: `{new_name}`"
                ),
                parse_mode='Markdown'
            )

        # Mesajları temizle
        await ask_msg.delete()
        await process_msg.delete()
        await update.message.delete()

        # Kullanıcı verisini temizle
        del context.user_data['waiting_rename']

    except Exception as e:
        await update.message.reply_text(f"❌ Dosya işlenirken hata oluştu: {str(e)}")

# Varsayılan thumb görüntüleme komutu
async def view_default_thumb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Varsayılan thumb'ı görüntüle"""
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    if not user_data.get("default_thumb"):
        await update.message.reply_text("❌ Kayıtlı varsayılan küçük resim bulunamadı!")
        return
        
    try:
        # Hex'ten binary'ye çevir
        thumb_content = bytes.fromhex(user_data["default_thumb"])
        
        # Küçük resmi hazırla
        thumb_image = Image.open(io.BytesIO(thumb_content))
        thumb_buffer = io.BytesIO()
        thumb_image.save(thumb_buffer, format='JPEG')
        thumb_buffer.seek(0)
        
        # Küçük resmi gönder
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=thumb_buffer,
            caption="🖼️ Mevcut varsayılan küçük resim",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Küçük resim görüntülenirken hata oluştu: {str(e)}")

# AI Sohbet Fonksiyonu
@require_credits('ai_chat')
async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yapay zeka ile sohbet"""
    user_id = update.effective_user.id
    is_member = await check_membership(user_id, context.bot, CHANNEL_USERNAME)

    if not is_member:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🔒 Lütfen botu kullanabilmek için {CHANNEL_USERNAME} kanalına katılın.",
            parse_mode='Markdown'
        )
        return

    if not context.args:
        await update.message.reply_text(
            "ℹ️ Lütfen bir soru veya istem girin:\n"
            "`/ai <mesajınız>`\n\n"
            "Diğer AI Komutları:\n"
            "- `/ai_clear`: Sohbet geçmişini temizler\n"
            "- `/ai_history`: Sohbet geçmişini gösterir\n\n"
            "Örnek: `/ai Python nedir?`",
            parse_mode='Markdown'
        )
        return

    command = context.args[0].lower()
    chat_history = ChatHistory(user_id)

    # Özel komutları kontrol et
    if command == 'clear':
        chat_history.clear()
        await update.message.reply_text("🗑️ Sohbet geçmişi temizlendi!")
        return
    elif command == 'history':
        context_text = chat_history.get_context()
        if context_text:
            await update.message.reply_text(
                f"📜 *Sohbet Geçmişi:*\n\n{context_text}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("📝 Henüz sohbet geçmişi yok.")
        return

    # Normal sohbet işlemi
    prompt = " ".join(context.args)
    
    try:
        wait_message = await update.message.reply_text(
            "🤔 Düşünüyorum...",
            parse_mode='Markdown'
        )

        # Geçmiş bağlamını ekle
        context_text = chat_history.get_context()
        if context_text:
            enhanced_prompt = f"{context_text}\n\nYeni soru: {prompt}\n\nYukarıdaki konuşma geçmişini dikkate alarak yanıt ver:"
        else:
            enhanced_prompt = prompt

        # API isteği
        api_url = "https://darkness.ashlynn.workers.dev/chat/"
        params = {
            "prompt": enhanced_prompt,
            "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "stream": "false",
            "temperature": 0.7
        }

        response = requests.get(
            api_url,
            params=params,
            headers={
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/json'
            },
            verify=False,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()

        await wait_message.delete()

        # Yanıtı işle ve gönder
        if data and isinstance(data, str):
            response_text = data
        elif data and isinstance(data, dict) and data.get("response"):
            response_text = data['response']
        else:
            response_text = "❌ Üzgünüm, yanıt alınamadı."

        # Geçmişe ekle
        chat_history.add_message('user', prompt)
        chat_history.add_message('assistant', response_text)

        # Yanıtı gönder
        await update.message.reply_text(
            f"🤖 *AI Yanıtı:*\n\n{response_text}",
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"AI sohbet hatası: {e}")
        await update.message.reply_text(
            "❌ Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin.",
            parse_mode='Markdown'
        )

# Yeni ayrı komutlar ekle
async def ai_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI sohbet geçmişini temizle"""
    user_id = update.effective_user.id
    chat_history = ChatHistory(user_id)
    chat_history.clear()
    await update.message.reply_text("🗑️ Sohbet geçmişi temizlendi!")

async def ai_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI sohbet geçmişini göster"""
    user_id = update.effective_user.id
    chat_history = ChatHistory(user_id)
    context_text = chat_history.get_context()
    
    if context_text:
        await update.message.reply_text(
            f"📜 *Sohbet Geçmişi:*\n\n{context_text}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("📝 Henüz sohbet geçmişi yok.")

# Admin komutları
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin paneli"""
    user = update.effective_user
    if not user_manager.is_admin(user.username):
        await update.message.reply_text("⛔️ Bu komutu kullanma yetkiniz yok!")
        return

    keyboard = [
        [
            InlineKeyboardButton("📢 Duyuru Yap", callback_data="admin_broadcast"),
            InlineKeyboardButton("👑 Premium Ver", callback_data="admin_premium")
        ],
        [
            InlineKeyboardButton("🚫 Kullanıcı Yasakla", callback_data="admin_ban"),
            InlineKeyboardButton("✅ Yasak Kaldır", callback_data="admin_unban")
        ],
        [
            InlineKeyboardButton("📊 İstatistikler", callback_data="admin_stats")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🔐 *Admin Paneli*\n\n"
        "Yapmak istediğiniz işlemi seçin:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# Ana Fonksiyon
async def main() -> None:
    application = None
    try:
        # Webhook'u temizle
        requests.get(f'https://api.telegram.org/bot{TOKEN}/deleteWebhook')
        
        # Basit yapılandırma
        application = (
            ApplicationBuilder()
            .token(TOKEN)
            .concurrent_updates(False)
            .connection_pool_size(8)
            .pool_timeout(30)
            .connect_timeout(30)
            .read_timeout(30)
            .write_timeout(30)
            .build()
        )

        # Handler'ları ekle
        handlers = [
            CommandHandler('start', start),
            CommandHandler('img', get_image),
            CommandHandler('kanal', channel_info),
            CommandHandler('rename', rename_file),
            CommandHandler('thumb', add_thumbnail),
            CommandHandler('del_thumb', delete_default_thumb),
            CommandHandler('view_thumb', view_default_thumb),
            CommandHandler('ai', ai_chat),
            CommandHandler('ai_clear', ai_clear),
            CommandHandler('ai_history', ai_history),
            CommandHandler('admin', admin_panel),
            MessageHandler((filters.PHOTO | filters.Document.ALL) & ~filters.COMMAND, process_file),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rename_response),
            CallbackQueryHandler(button_callback)
        ]

        for handler in handlers:
            application.add_handler(handler)

        logger.info("Bot başlatılıyor...")
        
        # Polling başlat
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
        # Sonsuz döngüde bekle
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Hata: {e}", exc_info=True)
    finally:
        if application:
            await application.stop()

if __name__ == '__main__':
    # Önceki process'leri temizle
    try:
        import psutil
        current_pid = os.getpid()
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == 'python' and proc.info['pid'] != current_pid:
                try:
                    os.kill(proc.info['pid'], 9)
                    logger.info(f"Eski process sonlandırıldı: {proc.info['pid']}")
                except:
                    pass
        time.sleep(2)  # Process'lerin kapanmasını bekle
    except:
        pass

    # Event loop'u temizle
    try:
        loop = asyncio.get_event_loop()
        loop.close()
    except:
        pass

    # Yeni event loop oluştur
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Botu başlat
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot kullanıcı tarafından durduruldu!")
    finally:
        loop.close()
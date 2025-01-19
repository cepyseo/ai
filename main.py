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
import sys
from flask import Flask, request
from threading import Thread
from quart import Quart, request
from hypercorn.config import Config
from hypercorn.asyncio import serve
import httpx
from config.settings import TOKEN, CONNECT_TIMEOUT, READ_TIMEOUT, WRITE_TIMEOUT, POOL_TIMEOUT
from web.app import create_app
from handlers.stats import show_stats
from handlers.callback_handlers import handle_callback_query
from handlers.chat_handlers import handle_chat
from services.user_service import UserService
from services.chat_service import ChatService

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

# Global application ve app değişkenleri
application = None
app = Quart(__name__)  # Quart app'i burada oluştur

# Dizin sabitleri
USER_DATA_DIR = Path("user_data")
CHAT_HISTORY_DIR = Path("chat_history")
USER_CREDITS_DIR = Path("user_credits")  # Eklendi

# Dizinleri oluştur
USER_DATA_DIR.mkdir(exist_ok=True)
CHAT_HISTORY_DIR.mkdir(exist_ok=True)
USER_CREDITS_DIR.mkdir(exist_ok=True)  # Eklendi

# Global servisleri oluştur
user_service = UserService()
chat_service = ChatService()

def setup_project():
    """Proje yapısını oluştur"""
    try:
        # Dizin yapılandırması
        directories = [
            'config',
            'handlers',
            'services',
            'utils',
            'web',
            'data/user_data',
            'data/chat_history',
            'data/user_credits',
            'data/backups',
            'data/lang'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            init_file = Path(directory) / '__init__.py'
            if not init_file.exists():
                init_file.touch()

        # Varsayılan dil dosyasını oluştur
        lang_file = Path('data/lang/tr.json')
        if not lang_file.exists():
            default_translations = {
                "welcome": "Hoş geldiniz!",
                "help": "Yardım menüsü",
                "settings": "Ayarlar",
                "error": "Bir hata oluştu",
                "success": "İşlem başarılı"
            }
            with open(lang_file, 'w', encoding='utf-8') as f:
                json.dump(default_translations, f, ensure_ascii=False, indent=2)
                
        logger.info("Proje yapısı başarıyla oluşturuldu")
        
    except Exception as e:
        logger.error(f"Proje yapısı oluşturulurken hata: {e}")
        raise

@app.route('/')
async def home():
    return "Bot çalışıyor!"

@app.route('/ping')
async def ping():
    return 'pong'

@app.route(f'/{TOKEN}', methods=['POST'])
async def webhook():
    """Telegram webhook handler"""
    try:
        if request.method == 'POST':
            json_data = await request.get_json()
            logger.info(f"Gelen webhook verisi: {json_data}")
            
            # Global application'ı kullan
            update = Update.de_json(json_data, application.bot)
            
            try:
                await application.process_update(update)
                logger.info(f"Update başarıyla işlendi: {update.update_id}")
            except Exception as e:
                logger.error(f"Update işleme hatası: {e}", exc_info=True)
            
            return 'OK'
    except Exception as e:
        logger.error(f"Webhook hatası: {e}", exc_info=True)
        return 'Error', 500

async def handle_update(update: Update):
    """Update'i işle"""
    try:
        await application.initialize()
        await application.process_update(update)
    except Exception as e:
        logger.error(f"Update işleme hatası: {e}")

def run_flask():
    # Render için port ayarı
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

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

# Admin callback handler'ını güncelle
async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin callback'lerini işle"""
    query = update.callback_query
    user = query.from_user
    
    # Admin kontrolü - kullanıcı adı ile kontrol
    if not user_manager.is_admin(user.username):
        await query.answer("⛔️ Bu işlem için yetkiniz yok!", show_alert=True)
        return
        
    try:
        if query.data == "admin_broadcast":
            context.user_data['admin_state'] = 'waiting_broadcast'
            await query.message.edit_text(
                "📢 Lütfen yayınlamak istediğiniz mesajı gönderin:\n"
                "(/cancel ile iptal edebilirsiniz)",
                reply_markup=None
            )
            
        elif query.data == "admin_premium":
            context.user_data['admin_state'] = 'waiting_premium_user'
            await query.message.edit_text(
                "👑 Premium vermek istediğiniz kullanıcının ID'sini gönderin:\n"
                "(/cancel ile iptal edebilirsiniz)",
                reply_markup=None
            )
            
        elif query.data == "admin_ban":
            context.user_data['admin_state'] = 'waiting_ban_user'
            await query.message.edit_text(
                "🚫 Yasaklamak istediğiniz kullanıcının ID'sini gönderin:\n"
                "(/cancel ile iptal edebilirsiniz)",
                reply_markup=None
            )
            
        elif query.data == "admin_unban":
            context.user_data['admin_state'] = 'waiting_unban_user'
            await query.message.edit_text(
                "✅ Yasağını kaldırmak istediğiniz kullanıcının ID'sini gönderin:\n"
                "(/cancel ile iptal edebilirsiniz)",
                reply_markup=None
            )
            
        elif query.data == "admin_stats":
            # İstatistikleri getir
            total_users = await user_service.get_total_users()
            active_users = await user_service.get_active_users_today()
            
            stats_text = (
                "📊 *Bot İstatistikleri*\n\n"
                f"👥 Toplam Kullanıcı: `{total_users}`\n"
                f"📱 Bugün Aktif: `{active_users}`\n"
                f"💾 Bellek Kullanımı: `{psutil.Process().memory_info().rss / 1024 / 1024:.1f} MB`\n"
                f"⏱️ Çalışma Süresi: `{datetime.now() - START_TIME}`"
            )
            
            await query.message.edit_text(
                stats_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Yenile", callback_data="admin_stats"),
                    InlineKeyboardButton("◀️ Geri", callback_data="admin_back")
                ]])
            )
            
        elif query.data == "admin_back":
            # Ana admin menüsüne dön
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
            
            await query.message.edit_text(
                "🔐 *Admin Paneli*\n\nYapmak istediğiniz işlemi seçin:",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
    except Exception as e:
        logger.error(f"Admin callback hatası: {e}")
        await query.answer("❌ Bir hata oluştu!", show_alert=True)

# Callback handler'ını güncelle
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback query'leri işle"""
    query = update.callback_query
    
    try:
        if query.data.startswith('admin_'):
            await handle_admin_callback(update, context)
        else:
            await query.answer()
            
            if query.data == "commands":
                # ... mevcut commands kodu ...
                pass
            elif query.data == "help":
                # ... mevcut help kodu ...
                pass
                
    except Exception as e:
        logger.error(f"Callback hatası: {e}")
        await query.answer("❌ Bir hata oluştu!", show_alert=True)

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
    """AI sohbeti başlat"""
    try:
        user_id = update.effective_user.id
        
        # Yasaklı kullanıcı kontrolü
        if user_manager.is_banned(user_id):
            await update.message.reply_text("⛔️ Bottan yasaklandınız!")
            return
            
        # AI sohbeti aktifleştir
        context.user_data['ai_chat_active'] = True
        
        await update.message.reply_text(
            "🤖 *AI Sohbet Başlatıldı*\n\n"
            "• Benimle istediğiniz konuda sohbet edebilirsiniz\n"
            "• Sohbeti sonlandırmak için /ai_clear yazın\n"
            "• Sohbet geçmişini görmek için /ai_history yazın",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"AI sohbet başlatma hatası: {e}")
        await update.message.reply_text("❌ Sohbet başlatılırken bir hata oluştu!")

# Yeni ayrı komutlar ekle
async def ai_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI sohbet geçmişini temizle"""
    try:
        user_id = update.effective_user.id
        
        # AI sohbeti deaktif et
        context.user_data['ai_chat_active'] = False
        
        # Sohbet geçmişini temizle
        await chat_service.clear_history(user_id)
        
        await update.message.reply_text(
            "🗑 Sohbet geçmişi temizlendi!\n"
            "Yeni bir sohbet başlatmak için /ai yazın."
        )
        
    except Exception as e:
        logger.error(f"Sohbet temizleme hatası: {e}")
        await update.message.reply_text("❌ Sohbet geçmişi temizlenirken bir hata oluştu!")

# AI History fonksiyonunu ekle
async def ai_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI sohbet geçmişini göster"""
    try:
        user_id = update.effective_user.id
        
        # Yasaklı kullanıcı kontrolü
        if user_manager.is_banned(user_id):
            await update.message.reply_text("⛔️ Bottan yasaklandınız!")
            return
            
        # Sohbet geçmişini al
        history = await chat_service.get_history(user_id)
        
        if not history:
            await update.message.reply_text(
                "📝 Henüz sohbet geçmişi yok.\n"
                "Sohbet başlatmak için /ai yazın."
            )
            return
            
        # Geçmişi formatlı şekilde göster
        history_text = "📜 *Sohbet Geçmişi*\n\n"
        
        for msg in history:
            if msg['role'] == 'user':
                history_text += f"👤 *Siz:* {msg['content']}\n\n"
            else:
                history_text += f"🤖 *Bot:* {msg['content']}\n\n"
        
        # Uzun mesajları böl
        if len(history_text) > 4000:
            history_text = history_text[:3997] + "..."
            
        await update.message.reply_text(
            history_text,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Sohbet geçmişi gösterme hatası: {e}")
        await update.message.reply_text(
            "❌ Sohbet geçmişi alınırken bir hata oluştu!"
        )

# Admin komutları
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin paneli"""
    user = update.effective_user
    
    # Admin kontrolü - kullanıcı adı ile kontrol
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

async def handle_admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin işlemlerini yöneten handler"""
    try:
        if not update.message or not update.message.text:
            return

        if 'admin_state' not in context.user_data:
            return
        
        if not user_manager.is_admin(update.effective_user.username):
            await update.message.reply_text("⛔️ Admin yetkisine sahip değilsiniz!")
            return

        state = context.user_data['admin_state']
        
        if state == 'waiting_broadcast':
            broadcast_msg = update.message.text
            if broadcast_msg.lower() == '/cancel':
                del context.user_data['admin_state']
                await update.message.reply_text("❌ Duyuru iptal edildi.")
                return

            status_msg = await update.message.reply_text("📢 Duyuru hazırlanıyor...")
            
            try:
                # Tüm kullanıcıları ve grupları topla
                all_targets = set()
                
                # Mevcut kullanıcıyı ekle
                all_targets.add(update.effective_chat.id)
                logger.info(f"Admin ID eklendi: {update.effective_chat.id}")
                
                # Dosya sisteminden kullanıcıları al
                for directory in [USER_DATA_DIR, CHAT_HISTORY_DIR, USER_CREDITS_DIR]:
                    if directory.exists():
                        logger.info(f"{directory} klasöründen kullanıcılar alınıyor...")
                        for file in directory.glob("*.json"):
                            try:
                                user_id = int(file.stem)
                                all_targets.add(user_id)
                                logger.info(f"Kullanıcı eklendi: {user_id}")
                            except ValueError:
                                continue
                
                # Premium kullanıcıları ekle
                if hasattr(user_manager, 'premium_users'):
                    logger.info("Premium kullanıcılar ekleniyor...")
                    for user_id in user_manager.premium_users:
                        try:
                            user_id = int(user_id)
                            all_targets.add(user_id)
                            logger.info(f"Premium kullanıcı eklendi: {user_id}")
                        except (ValueError, TypeError):
                            continue
                
                # Kanal ve grup bilgilerini al
                try:
                    # Kanal bilgisini al
                    channel = await context.bot.get_chat(CHANNEL_USERNAME)
                    all_targets.add(channel.id)
                    logger.info(f"Kanal eklendi: {channel.id}")
                    
                    # Kanalın üyelerini al
                    members = await context.bot.get_chat_administrators(CHANNEL_USERNAME)
                    for member in members:
                        if member.user.id != context.bot.id:  # Bot'un kendisi hariç
                            all_targets.add(member.user.id)
                            logger.info(f"Kanal üyesi eklendi: {member.user.id}")
                            
                except Exception as e:
                    logger.error(f"Kanal bilgileri alınamadı: {e}")
                
                logger.info(f"Hedef listesi: {all_targets}")
                total_targets = len(all_targets)
                
                if total_targets == 0:
                    await status_msg.edit_text("❌ Duyuru gönderilebilecek hedef bulunamadı!")
                    del context.user_data['admin_state']
                    return
                
                await status_msg.edit_text(f"📢 Duyuru gönderiliyor... (0/{total_targets})")
                
                success = 0
                failed = 0
                
                # Her hedef için duyuru gönder
                for target_id in all_targets:
                    try:
                        # Her hedef için yeni bir bot instance'ı kullan
                        bot = context.bot._bot
                        await bot.send_message(
                            chat_id=target_id,
                            text=f"📢 *DUYURU*\n\n{broadcast_msg}",
                            parse_mode='Markdown'
                        )
                        success += 1
                        logger.info(f"Duyuru başarıyla gönderildi: {target_id}")
                    except Exception as e:
                        logger.error(f"Duyuru gönderme hatası (Target: {target_id}): {e}")
                        failed += 1
                    finally:
                        await asyncio.sleep(0.05)
                        if success % 5 == 0 or success + failed == total_targets:
                            try:
                                await status_msg.edit_text(
                                    f"📤 Duyuru gönderiliyor... ({success}/{total_targets})"
                                )
                            except Exception as e:
                                logger.error(f"Durum mesajı güncellenemedi: {e}")
                
                try:
                    await status_msg.edit_text(
                        f"📊 *Duyuru Tamamlandı*\n\n"
                        f"✅ Başarılı: {success}\n"
                        f"❌ Başarısız: {failed}\n"
                        f"👥 Toplam: {total_targets}",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Son durum mesajı güncellenemedi: {e}")
                
            except Exception as e:
                logger.error(f"Duyuru işlemi hatası: {e}")
                try:
                    await status_msg.edit_text(
                        f"❌ *Duyuru Gönderilirken Hata Oluştu*\n\n"
                        f"Hata: {str(e)}",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Hata mesajı gönderilemedi: {e}")
            finally:
                if 'admin_state' in context.user_data:
                    del context.user_data['admin_state']
        
        elif state == 'waiting_premium_user':
            try:
                user_id = int(update.message.text)
                user_manager.add_premium(user_id)
                await update.message.reply_text(f"✅ {user_id} ID'li kullanıcıya premium verildi!")
            except ValueError:
                await update.message.reply_text("❌ Geçersiz kullanıcı ID'si!")
            finally:
                del context.user_data['admin_state']
        
        elif state == 'waiting_ban_user':
            try:
                user_id = int(update.message.text)
                user_manager.ban_user(user_id)
                await update.message.reply_text(f"🚫 {user_id} ID'li kullanıcı yasaklandı!")
            except ValueError:
                await update.message.reply_text("❌ Geçersiz kullanıcı ID'si!")
            finally:
                del context.user_data['admin_state']
        
        elif state == 'waiting_unban_user':
            try:
                user_id = int(update.message.text)
                user_manager.unban_user(user_id)
                await update.message.reply_text(f"✅ {user_id} ID'li kullanıcının yasağı kaldırıldı!")
            except ValueError:
                await update.message.reply_text("❌ Geçersiz kullanıcı ID'si!")
            finally:
                del context.user_data['admin_state']
                
    except Exception as e:
        logger.error(f"Admin handler hatası: {e}")
        if 'admin_state' in context.user_data:
            del context.user_data['admin_state']

async def cancel_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin işlemini iptal et"""
    if 'admin_state' in context.user_data:
        del context.user_data['admin_state']
        await update.message.reply_text("❌ İşlem iptal edildi.")
    else:
        await update.message.reply_text("ℹ️ İptal edilecek bir işlem yok.")

# Webhook ve keep-alive için yeni ayarlar
async def setup_webhook(application):
    """Webhook'u ayarla"""
    try:
        WEBHOOK_URL = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
        
        # Önce mevcut webhook'u temizle
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Eski webhook temizlendi")
        
        # Yeni webhook'u ayarla
        success = await application.bot.set_webhook(
            url=WEBHOOK_URL,
            allowed_updates=['message', 'callback_query', 'channel_post', 'edited_message'],
            drop_pending_updates=True,
            max_connections=100
        )
        
        if success:
            logger.info(f"Webhook başarıyla ayarlandı: {WEBHOOK_URL}")
        else:
            logger.error("Webhook ayarlanamadı!")
            
        # Webhook bilgisini kontrol et
        webhook_info = await application.bot.get_webhook_info()
        logger.info(f"Webhook durumu: {webhook_info.to_dict()}")
        
    except Exception as e:
        logger.error(f"Webhook ayarlama hatası: {e}", exc_info=True)
        raise

# Ağ ayarları ve timeout sabitleri
CONNECT_TIMEOUT = 30.0  # Bağlantı timeout süresi
READ_TIMEOUT = 30.0    # Okuma timeout süresi
WRITE_TIMEOUT = 30.0   # Yazma timeout süresi
POOL_TIMEOUT = 30.0    # Havuz timeout süresi

# Port ayarları
PORT = int(os.environ.get("PORT", 10000))  # Render için varsayılan port

async def init_application():
    """Bot uygulamasını başlat"""
    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .connect_timeout(CONNECT_TIMEOUT)
        .read_timeout(READ_TIMEOUT)
        .write_timeout(WRITE_TIMEOUT)
        .pool_timeout(POOL_TIMEOUT)
        .connection_pool_size(100)
        .concurrent_updates(True)
        .build()
    )
    
    # Handler'ları ekle
    handlers = [
        CommandHandler('start', start),
        CommandHandler('admin', admin_panel),
        CommandHandler('cancel', cancel_admin_action),
        CommandHandler('ai', ai_chat),
        CommandHandler('ai_clear', ai_clear),
        CommandHandler('ai_history', ai_history),
        CommandHandler('img', get_image),
        CommandHandler('stats', show_stats),
        CommandHandler('thumb', add_thumbnail),
        CommandHandler('del_thumb', delete_default_thumb),
        CommandHandler('view_thumb', view_default_thumb),
        CallbackQueryHandler(handle_callback_query),  # Callback'leri önce işle
        MessageHandler((filters.PHOTO | filters.Document.ALL) & ~filters.COMMAND, process_file),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat)  # En son normal mesajları işle
    ]

    for handler in handlers:
        application.add_handler(handler)

    # Hata handler'ını ekle
    application.add_error_handler(error_handler)

    return application

async def main():
    try:
        global application
        
        # Proje yapısını oluştur
        setup_project()
        logger.info("Proje yapısı oluşturuldu")
        
        # Bot'u başlat
        application = await init_application()
        await application.initialize()
        logger.info("Bot başlatıldı")
        
        # Webhook'u ayarla
        await setup_webhook(application)
        
        # Bot'u başlat
        await application.start()
        logger.info("Application başlatıldı")
        
        # Web uygulamasını başlat
        app.bot_application = application  # Global app'e application'ı ekle
        
        # Hypercorn config
        config = Config()
        config.bind = [f"0.0.0.0:{PORT}"]
        config.use_reloader = False
        
        logger.info(f"Web uygulaması {PORT} portunda başlatılıyor...")
        await serve(app, config)
        
    except Exception as e:
        logger.error(f"Kritik hata: {e}", exc_info=True)
        raise

# Quart app ayarlarını güncelle
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
app.config['PROPAGATE_EXCEPTIONS'] = True

if __name__ == '__main__':
    retry_count = 0
    max_retries = 5
    
    while retry_count < max_retries:
        try:
            asyncio.run(main())
            break
        except Exception as e:
            retry_count += 1
            logger.error(f"Yeniden başlatılıyor ({retry_count}/{max_retries})")
            time.sleep(5 * retry_count)
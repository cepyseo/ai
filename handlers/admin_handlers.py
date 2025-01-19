import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.backup_service import BackupService
from services.user_service import UserService
from admin_utils import UserManager
import asyncio
from datetime import datetime
import psutil

logger = logging.getLogger(__name__)
backup_service = BackupService()
user_service = UserService()
user_manager = UserManager()

async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin dashboard"""
    try:
        if not user_service.is_admin(update.effective_user.id):
            await update.message.reply_text("⛔️ Bu komutu kullanma yetkiniz yok!")
            return
            
        # İstatistikleri al
        total_users = await user_service.get_total_users()
        active_users = await user_service.get_active_users_today()
        premium_users = await user_service.get_premium_users()
        
        dashboard_text = (
            "📊 *Admin Dashboard*\n\n"
            f"👥 Toplam Kullanıcı: `{total_users}`\n"
            f"📱 Aktif Kullanıcı: `{active_users}`\n"
            f"👑 Premium Üye: `{premium_users}`\n\n"
            "Son Yedekleme:\n"
            f"🗓 {await get_last_backup_date()}"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Yedek Al", callback_data="admin_backup"),
                InlineKeyboardButton("📊 Detaylı İstatistik", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton("👥 Kullanıcı Listesi", callback_data="admin_users"),
                InlineKeyboardButton("⚙️ Ayarlar", callback_data="admin_settings")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            dashboard_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Dashboard hatası: {e}")
        await update.message.reply_text("❌ Dashboard yüklenirken bir hata oluştu!")

async def get_last_backup_date() -> str:
    """Son yedekleme tarihini getir"""
    try:
        backup_files = list(BACKUP_DIR.glob('backup_*'))
        if not backup_files:
            return "Henüz yedek yok"
            
        latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
        backup_time = datetime.fromtimestamp(latest_backup.stat().st_mtime)
        return backup_time.strftime('%d.%m.%Y %H:%M')
        
    except Exception as e:
        logger.error(f"Yedek tarihi alma hatası: {e}")
        return "Bilinmiyor"

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
                # Tüm kullanıcıları al
                all_users = await user_service.get_all_users()
                total_users = len(all_users)
                
                if total_users == 0:
                    await status_msg.edit_text("❌ Duyuru gönderilebilecek kullanıcı bulunamadı!")
                    del context.user_data['admin_state']
                    return
                
                success = 0
                failed = 0
                
                # Her kullanıcıya duyuru gönder
                for user_id in all_users:
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=f"📢 *DUYURU*\n\n{broadcast_msg}",
                            parse_mode='Markdown'
                        )
                        success += 1
                        logger.info(f"Duyuru başarıyla gönderildi: {user_id}")
                    except Exception as e:
                        logger.error(f"Duyuru gönderme hatası (User: {user_id}): {e}")
                        failed += 1
                    finally:
                        if success % 5 == 0:
                            await status_msg.edit_text(
                                f"📤 Duyuru gönderiliyor... ({success}/{total_users})"
                            )
                        await asyncio.sleep(0.05)
                
                await status_msg.edit_text(
                    f"✅ Duyuru tamamlandı!\n\n"
                    f"Başarılı: {success}\n"
                    f"Başarısız: {failed}\n"
                    f"Toplam: {total_users}"
                )
                
            except Exception as e:
                logger.error(f"Duyuru işlemi hatası: {e}")
                await status_msg.edit_text("❌ Duyuru gönderilirken bir hata oluştu!")
            finally:
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
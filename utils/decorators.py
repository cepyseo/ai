import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

def require_premium():
    """Premium kullanıcı gerektiren işlemler için dekoratör"""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            # Premium kontrol kodları...
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator 
# -*- coding: utf-8 -*-
import os
import sys

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import threading
import asyncio
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

TOKEN = os.getenv('DISCORD_TOKEN')
PORT = int(os.getenv('PORT', 5050))

def start_bot_worker():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        from bot import bot
        print('[BULUT MOTORU] Discord Botu arka planda başlatılıyor...')
        loop.run_until_complete(bot.start(TOKEN))
    except Exception as e:
        print('[BULUT MOTORU] Bot başlatma hatası:', e)

if __name__ == '__main__':
    if not TOKEN:
        print('HATA: DISCORD_TOKEN bulunamadı!')
        sys.exit(1)

    bot_thread = threading.Thread(target=start_bot_worker, daemon=True)
    bot_thread.start()

    from dashboard import app
    print('=======================================================')
    print('  🌐 Ala Cafe 7/24 Birleşik Bulut Motoru Aktif!')
    print(f'  👉 Web Dashboard Portu: {PORT}')
    print('=======================================================')
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

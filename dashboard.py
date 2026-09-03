import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import time
import json
import sqlite3
import subprocess
import psutil
from functools import wraps
from flask import Flask, render_template, request, jsonify, send_file, session

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "ala_cafe_super_secret_session_key_2026")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ala2026")

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return jsonify({"success": False, "error": "Yetkisiz erişim! Lütfen giriş yapın."}), 401
        return f(*args, **kwargs)
    return decorated

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "data", "bot.log")
BOT_SCRIPT = os.path.join(BASE_DIR, "bot.py")
TRANSCRIPTS_DIR = os.path.join(BASE_DIR, "data", "transcripts")
DB_PATH = os.path.join(BASE_DIR, "data", "cafe.db")

def get_bot_process():
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmd = p.info.get('cmdline') or []
            if any('bot.py' in str(arg) for arg in cmd):
                return p
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None

def is_bot_running():
    return get_bot_process() is not None

# --- Kimlik Doğrulama & Güvenlik Kapısı ---
@app.route("/api/auth/check")
def api_auth_check():
    return jsonify({"authenticated": bool(session.get("authenticated"))})

@app.route("/api/auth/login", methods=["POST"])
def api_auth_login():
    data = request.json or {}
    password = data.get("password", "")
    if password == ADMIN_PASSWORD:
        session["authenticated"] = True
        return jsonify({"success": True, "message": "Giriş başarılı!"})
    return jsonify({"success": False, "error": "Hatalı şifre!"}), 401

@app.route("/api/auth/logout", methods=["POST"])
def api_auth_logout():
    session.pop("authenticated", None)
    return jsonify({"success": True, "message": "Çıkış yapıldı."})

# --- Sayfa Yönlendirmesi ---
@app.route("/")
def index():
    return render_template("index.html")

# --- API: Bot Durumu ve Sistem ---
@app.route("/api/status")
@login_required
def api_status():
    p = get_bot_process()
    running = p is not None
    cpu_percent = psutil.cpu_percent()
    ram = psutil.virtual_memory()

    return jsonify({
        "running": running,
        "pid": p.pid if p else None,
        "cpu": cpu_percent,
        "ram_percent": ram.percent,
        "ram_used_mb": round(ram.used / (1024 * 1024)),
        "ram_total_mb": round(ram.total / (1024 * 1024)),
        "server_name": "Ala Lounge",
        "bot_name": "Ala Cafe Çalışanı v4.0"
    })

# --- API: Bot Başlat / Durdur / Yeniden Başlat ---
@app.route("/api/bot/<action>", methods=["POST"])
@login_required
def api_bot_action(action):
    try:
        if action == "start":
            if not is_bot_running():
                py_exe = sys.executable.replace("pythonw.exe", "python.exe")
                subprocess.Popen(
                    [py_exe, BOT_SCRIPT],
                    cwd=BASE_DIR,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                )
                time.sleep(1)
            return jsonify({"success": True, "message": "Bot başlatıldı!"})

        elif action == "stop":
            for p in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmd = p.info.get('cmdline') or []
                    if any('bot.py' in str(arg) for arg in cmd):
                        p.kill()
                except Exception:
                    pass
            return jsonify({"success": True, "message": "Bot durduruldu!"})

        elif action == "restart":
            for p in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmd = p.info.get('cmdline') or []
                    if any('bot.py' in str(arg) for arg in cmd):
                        p.kill()
                except Exception:
                    pass
            time.sleep(1.5)
            py_exe = sys.executable.replace("pythonw.exe", "python.exe")
            subprocess.Popen(
                [py_exe, BOT_SCRIPT],
                cwd=BASE_DIR,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            return jsonify({"success": True, "message": "Bot yeniden başlatıldı!"})

        return jsonify({"success": False, "error": "Geçersiz eylem"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# --- API: Özelleştirme & Karşılama Stüdyosu ---
@app.route("/api/customizations", methods=["GET", "POST"])
@login_required
def api_customizations():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS bot_customizations (key TEXT PRIMARY KEY, value TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS guild_settings (guild_id INTEGER PRIMARY KEY, welcome_channel_id INTEGER, auto_role_id INTEGER, log_channel_id INTEGER, ticket_category_id INTEGER)")

    if request.method == "GET":
        c.execute("SELECT key, value FROM bot_customizations")
        rows = c.fetchall()
        data = {r[0]: r[1] for r in rows}

        c.execute("SELECT welcome_channel_id, auto_role_id FROM guild_settings LIMIT 1")
        g_row = c.fetchone()
        conn.close()

        welcome_ch = g_row[0] if g_row and g_row[0] else ""
        auto_role = g_row[1] if g_row and g_row[1] else ""

        return jsonify({
            "welcome_title": data.get("welcome_title", "☕ Ala Lounge'a Hoş Geldiniz!"),
            "welcome_message": data.get("welcome_message", "Aramıza hoş geldin {kullanici}! Boş masalara geçebilir, sıcak muhabbetimize katılabilirsin. Sunucumuz seninle beraber {uye_sayisi} kişi oldu! 💨"),
            "bot_activity": data.get("bot_activity", "Ala Lounge & Nargile Masalarını 💨 | /oynat"),
            "default_volume": int(data.get("default_volume", 80)),
            "welcome_channel_id": str(welcome_ch),
            "auto_role_id": str(auto_role)
        })

    elif request.method == "POST":
        req = request.json or {}
        items = [
            ("welcome_title", req.get("welcome_title", "")),
            ("welcome_message", req.get("welcome_message", "")),
            ("bot_activity", req.get("bot_activity", "")),
            ("default_volume", str(req.get("default_volume", 80)))
        ]
        for k, v in items:
            c.execute("INSERT INTO bot_customizations (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=?", (k, v, v))

        # Sunucu ayarları (kanal ve rol)
        wch = req.get("welcome_channel_id")
        arole = req.get("auto_role_id")
        try:
            wch_int = int(wch) if wch and str(wch).isdigit() else None
            arole_int = int(arole) if arole and str(arole).isdigit() else None
            c.execute("""
                INSERT INTO guild_settings (guild_id, welcome_channel_id, auto_role_id)
                VALUES (1112406647738994718, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    welcome_channel_id = COALESCE(excluded.welcome_channel_id, guild_settings.welcome_channel_id),
                    auto_role_id = COALESCE(excluded.auto_role_id, guild_settings.auto_role_id)
            """, (wch_int, arole_int))
        except Exception as e:
            print("Kanal/rol kaydetme hatası:", e)

        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Ayarlar başarıyla kaydedildi!"})

# --- API: VIP & Yönetim Kadrosu ---
@app.route("/api/vips", methods=["GET", "POST"])
@login_required
def api_vips():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS vip_members (user_id INTEGER PRIMARY KEY, name TEXT, title TEXT, notes TEXT, added_at TEXT)")

    if request.method == "GET":
        c.execute("SELECT * FROM vip_members ORDER BY added_at DESC")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify(rows)

    elif request.method == "POST":
        req = request.json or {}
        uid = req.get("user_id")
        name = req.get("name")
        title = req.get("title")
        notes = req.get("notes", "")

        if not uid or not name or not title:
            conn.close()
            return jsonify({"success": False, "error": "ID, İsim ve Unvan zorunludur"}), 400

        now = time.strftime("%Y-%m-%d %H:%M")
        c.execute("""
            INSERT INTO vip_members (user_id, name, title, notes, added_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET name=?, title=?, notes=?
        """, (int(uid), name, title, notes, now, name, title, notes))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "VIP üye kaydedildi!"})

@app.route("/api/vips/<int:user_id>", methods=["DELETE"])
@login_required
def api_delete_vip(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM vip_members WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Kişi silindi!"})

# --- API: Chat Dökümleri ---
@app.route("/api/transcripts")
@login_required
def api_transcripts():
    files = []
    if os.path.exists(TRANSCRIPTS_DIR):
        for f in sorted(os.listdir(TRANSCRIPTS_DIR), reverse=True):
            if f.endswith(".txt"):
                path = os.path.join(TRANSCRIPTS_DIR, f)
                stat = os.stat(path)
                files.append({
                    "name": f,
                    "size_kb": round(stat.st_size / 1024, 1),
                    "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(stat.st_mtime))
                })
    return jsonify(files)

@app.route("/api/transcripts/<filename>")
@login_required
def api_transcript_view(filename):
    safe_name = os.path.basename(filename)
    path = os.path.join(TRANSCRIPTS_DIR, safe_name)
    if not os.path.exists(path):
        return jsonify({"error": "Dosya bulunamadı"}), 404

    if request.args.get("download") == "1":
        return send_file(path, as_attachment=True)

    with open(path, "r", encoding="utf-8", errors="ignore") as fp:
        content = fp.read()
    return jsonify({"name": safe_name, "content": content})

# --- API: Canlı Konsol Logları ---
@app.route("/api/logs")
@login_required
def api_logs():
    lines = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                all_lines = f.readlines()
                lines = all_lines[-100:]
        except Exception:
            pass
    return jsonify({"logs": lines})

# --- API: Müdavim Liderlik Tablosu ---
@app.route("/api/leaderboard")
@login_required
def api_leaderboard():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS user_levels (user_id INTEGER, guild_id INTEGER, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, last_msg_xp REAL DEFAULT 0, voice_joined_at REAL DEFAULT 0, PRIMARY KEY (user_id, guild_id))")
    c.execute("SELECT user_id, xp, level FROM user_levels ORDER BY xp DESC LIMIT 10")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

if __name__ == "__main__":
    print("=======================================================")
    print("  🌐 Ala Cafe Güvenli Web Dashboard Başlatıldı!")
    print("  👉 Varsayılan Şifre: ala2026 (Render ADMIN_PASSWORD)")
    print("=======================================================")
    app.run(host="127.0.0.1", port=5050, debug=False)

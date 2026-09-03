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
import io
import math
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

# --- Kimlik Doğrulama ---
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

# --- Sayfa ---
@app.route("/")
def index():
    return render_template("index.html")

# --- 1. Master İstatistikler ---
@app.route("/api/master-stats")
@login_required
def api_master_stats():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS command_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, user_name TEXT, command_name TEXT, command_args TEXT, channel_name TEXT, guild_id INTEGER, executed_at TEXT)")
    c.execute("SELECT COUNT(*) as cnt FROM command_logs")
    total_cmds = c.fetchone()["cnt"]

    c.execute("CREATE TABLE IF NOT EXISTS ticket_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_channel_id INTEGER UNIQUE, ticket_name TEXT, user_id INTEGER, user_name TEXT, opened_at TEXT, closed_at TEXT, closed_by TEXT, transcript_text TEXT, status TEXT DEFAULT 'AÇIK')")
    c.execute("SELECT COUNT(*) as open_cnt FROM ticket_logs WHERE status = 'AÇIK'")
    open_tickets = c.fetchone()["open_cnt"]
    c.execute("SELECT COUNT(*) as closed_cnt FROM ticket_logs WHERE status = 'KAPALI'")
    closed_tickets = c.fetchone()["closed_cnt"]

    c.execute("CREATE TABLE IF NOT EXISTS temp_tables (channel_id INTEGER PRIMARY KEY, guild_id INTEGER, owner_id INTEGER, created_at TEXT)")
    c.execute("SELECT COUNT(*) as tbl_cnt FROM temp_tables")
    active_tables = c.fetchone()["tbl_cnt"]

    c.execute("CREATE TABLE IF NOT EXISTS user_levels (user_id INTEGER, guild_id INTEGER, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, last_msg_xp REAL DEFAULT 0, voice_joined_at REAL DEFAULT 0, PRIMARY KEY (user_id, guild_id))")
    c.execute("SELECT COUNT(*) as lvl_cnt FROM user_levels")
    total_members = c.fetchone()["lvl_cnt"]

    c.execute("SELECT command_name, COUNT(*) as cnt FROM command_logs GROUP BY command_name ORDER BY cnt DESC LIMIT 5")
    top_cmds = [dict(r) for r in c.fetchall()]

    c.execute("SELECT user_name, user_id, COUNT(*) as cnt FROM command_logs GROUP BY user_id ORDER BY cnt DESC LIMIT 5")
    top_users = [dict(r) for r in c.fetchall()]

    conn.close()

    p = get_bot_process()
    ram = psutil.virtual_memory()

    return jsonify({
        "total_commands": total_cmds,
        "open_tickets": open_tickets,
        "closed_tickets": closed_tickets,
        "active_tables": active_tables,
        "total_members": total_members,
        "top_commands": top_cmds,
        "top_users": top_users,
        "cpu": psutil.cpu_percent(),
        "ram": ram.percent,
        "bot_running": p is not None
    })

# --- 2. Komut Günlükleri (Audit Logs) ---
@app.route("/api/command-logs")
@login_required
def api_command_logs():
    search = request.args.get("search", "").strip()
    limit = int(request.args.get("limit", 150))
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS command_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, user_name TEXT, command_name TEXT, command_args TEXT, channel_name TEXT, guild_id INTEGER, executed_at TEXT)")
    
    if search:
        c.execute("""
            SELECT * FROM command_logs 
            WHERE user_name LIKE ? OR command_name LIKE ? OR command_args LIKE ? OR channel_name LIKE ?
            ORDER BY id DESC LIMIT ?
        """, (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%", limit))
    else:
        c.execute("SELECT * FROM command_logs ORDER BY id DESC LIMIT ?", (limit,))
        
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route("/api/command-logs/export")
@login_required
def api_export_command_logs():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM command_logs ORDER BY id DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()

    output = ["ID | Tarih | Kullanıcı (ID) | Komut | Parametreler | Kanal"]
    output.append("=" * 100)
    for r in rows:
        output.append(f"{r['id']} | {r['executed_at']} | {r['user_name']} ({r['user_id']}) | /{r['command_name']} | {r['command_args']} | #{r['channel_name']}")
    
    text_data = "\n".join(output)
    return send_file(io.BytesIO(text_data.encode("utf-8")), mimetype="text/plain", as_attachment=True, download_name=f"komut_gecmisi_{int(time.time())}.txt")

@app.route("/api/command-logs/clear", methods=["POST"])
@login_required
def api_clear_command_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM command_logs")
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Komut geçmişi temizlendi."})

# --- 3. Destek Biletleri & Transkriptler ---
@app.route("/api/tickets")
@login_required
def api_tickets():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS ticket_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_channel_id INTEGER UNIQUE, ticket_name TEXT, user_id INTEGER, user_name TEXT, opened_at TEXT, closed_at TEXT, closed_by TEXT, transcript_text TEXT, status TEXT DEFAULT 'AÇIK')")
    c.execute("SELECT id, ticket_channel_id, ticket_name, user_id, user_name, opened_at, closed_at, closed_by, status FROM ticket_logs ORDER BY id DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route("/api/tickets/<int:ticket_id>")
@login_required
def api_ticket_detail(ticket_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM ticket_logs WHERE id = ?", (ticket_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Bilet bulunamadı"}), 404
    return jsonify(dict(row))

# --- 4. Sanal Masalar ---
@app.route("/api/tables", methods=["GET"])
@login_required
def api_tables():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS temp_tables (channel_id INTEGER PRIMARY KEY, guild_id INTEGER, owner_id INTEGER, created_at TEXT)")
    c.execute("SELECT * FROM temp_tables ORDER BY created_at DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route("/api/tables/<int:channel_id>", methods=["DELETE"])
@login_required
def api_delete_table(channel_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM temp_tables WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Masa kaydı sonlandırıldı."})

# --- 5. Müdavim Seviye / XP Yönetimi ---
@app.route("/api/leaderboard")
@login_required
def api_leaderboard():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS user_levels (user_id INTEGER, guild_id INTEGER, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, last_msg_xp REAL DEFAULT 0, voice_joined_at REAL DEFAULT 0, PRIMARY KEY (user_id, guild_id))")
    c.execute("SELECT user_id, xp, level FROM user_levels ORDER BY xp DESC LIMIT 25")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route("/api/leaderboard/edit", methods=["POST"])
@login_required
def api_leaderboard_edit():
    data = request.json or {}
    uid = data.get("user_id")
    new_xp = data.get("xp")
    if not uid or new_xp is None:
        return jsonify({"success": False, "error": "Geçersiz parametre"}), 400

    new_xp = int(new_xp)
    new_level = max(1, int(math.sqrt(new_xp / 100)))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE user_levels SET xp = ?, level = ? WHERE user_id = ?", (new_xp, new_level, int(uid)))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Üyenin XP'si {new_xp} (Seviye {new_level}) olarak güncellendi!"})

# --- 6. Ziya Ortak AI Web Sohbet Konsolu ---
@app.route("/api/ziya/chat", methods=["POST"])
@login_required
def api_ziya_chat():
    data = request.json or {}
    msg = data.get("message", "").strip()
    if not msg:
        return jsonify({"success": False, "error": "Mesaj boş olamaz"}), 400

    from dotenv import dotenv_values
    import urllib.request
    env = dotenv_values(os.path.join(BASE_DIR, ".env"))
    key = env.get("GEMINI_API_KEY")
    if not key:
        return jsonify({"success": False, "error": "GEMINI_API_KEY bulunamadı"}), 500

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={key}"
    sys_prompt = "Sen Ala Lounge'ın bilge, görmüş geçirmiş, dobra ortağı 'Ziya Ortak'sın. Web kontrol panelinden seninle konuşuluyor. Samimi, esprili, babacan ve dobra bir şekilde 'Eyvallah ortak, bak mevzu şöyle...' diyerek kısa ve vurucu (1-2 paragraf) yanıt ver. Yalakalık yapma."

    payload = {
        "system_instruction": {"parts": [{"text": sys_prompt}]},
        "contents": [{"parts": [{"text": msg}]}]
    }

    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_data = json.loads(resp.read().decode())
            text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            return jsonify({"success": True, "reply": text})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# --- 7. Bot Kontrol & Loglar ---
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
        "bot_name": "Ala Cafe Çalışanı v5.7"
    })

@app.route("/api/bot/<action>", methods=["POST"])
@login_required
def api_bot_action(action):
    try:
        if action == "start":
            if not is_bot_running():
                cmd = ["pythonw.exe", BOT_SCRIPT] if sys.platform == "win32" else ["python3", BOT_SCRIPT]
                subprocess.Popen(cmd, cwd=BASE_DIR)
                return jsonify({"success": True, "message": "Bot başlatıldı!"})
            return jsonify({"success": False, "error": "Bot zaten çalışıyor!"})

        elif action == "stop":
            p = get_bot_process()
            if p:
                p.terminate()
                p.wait(timeout=5)
                return jsonify({"success": True, "message": "Bot durduruldu!"})
            return jsonify({"success": False, "error": "Bot zaten çalışmıyor!"})

        elif action == "restart":
            p = get_bot_process()
            if p:
                p.terminate()
                try:
                    p.wait(timeout=5)
                except Exception:
                    p.kill()
            cmd = ["pythonw.exe", BOT_SCRIPT] if sys.platform == "win32" else ["python3", BOT_SCRIPT]
            subprocess.Popen(cmd, cwd=BASE_DIR)
            return jsonify({"success": True, "message": "Bot yeniden başlatıldı!"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/logs")
@login_required
def api_logs():
    lines = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[-120:]
        except Exception:
            pass
    return jsonify({"logs": lines})

# --- 8. Özelleştirmeler & VIP & Transkriptler ---
@app.route("/api/settings", methods=["GET", "POST"])
@login_required
def api_settings():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS bot_customizations (key TEXT PRIMARY KEY, value TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS guild_settings (guild_id INTEGER PRIMARY KEY, welcome_channel_id INTEGER, auto_role_id INTEGER)")

    if request.method == "GET":
        c.execute("SELECT key, value FROM bot_customizations")
        customs = {r["key"]: r["value"] for r in c.fetchall()}
        c.execute("SELECT welcome_channel_id, auto_role_id FROM guild_settings WHERE guild_id = 1112406647738994718")
        row = c.fetchone()
        conn.close()
        return jsonify({
            "welcome_title": customs.get("welcome_title", "☕ Hoş Geldin Değerli Dostum!"),
            "welcome_message": customs.get("welcome_message", "{user}, **Ala Lounge & Cafe** masamıza teşrif ettin!"),
            "welcome_channel_id": str(row["welcome_channel_id"]) if row and row["welcome_channel_id"] else "",
            "auto_role_id": str(row["auto_role_id"]) if row and row["auto_role_id"] else ""
        })

    elif request.method == "POST":
        data = request.json or {}
        w_title = data.get("welcome_title", "")
        w_msg = data.get("welcome_message", "")
        w_chan = data.get("welcome_channel_id", "").strip()
        a_role = data.get("auto_role_id", "").strip()

        c.execute("INSERT OR REPLACE INTO bot_customizations (key, value) VALUES ('welcome_title', ?)", (w_title,))
        c.execute("INSERT OR REPLACE INTO bot_customizations (key, value) VALUES ('welcome_message', ?)", (w_msg,))

        wch_int = int(w_chan) if w_chan.isdigit() else None
        arole_int = int(a_role) if a_role.isdigit() else None
        c.execute("""
            INSERT INTO guild_settings (guild_id, welcome_channel_id, auto_role_id)
            VALUES (1112406647738994718, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                welcome_channel_id = COALESCE(excluded.welcome_channel_id, guild_settings.welcome_channel_id),
                auto_role_id = COALESCE(excluded.auto_role_id, guild_settings.auto_role_id)
        """, (wch_int, arole_int))

        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Ayarlar başarıyla kaydedildi!"})

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
            return jsonify({"success": False, "error": "Eksik bilgi"}), 400
        now = time.strftime("%Y-%m-%d %H:%M")
        c.execute("INSERT INTO vip_members (user_id, name, title, notes, added_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET name=?, title=?, notes=?", (int(uid), name, title, notes, now, name, title, notes))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Kaydedildi!"})

@app.route("/api/vips/<int:user_id>", methods=["DELETE"])
@login_required
def api_delete_vip(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM vip_members WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Silindi!"})

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

if __name__ == "__main__":
    print("=======================================================")
    print("  🌐 Ala Cafe Master Web Dashboard v6.0 Başlatıldı!")
    print("  👉 Adres: http://127.0.0.1:5050")
    print("  👉 Varsayılan Şifre: ala2026")
    print("=======================================================")
    app.run(host="127.0.0.1", port=5050, debug=False)

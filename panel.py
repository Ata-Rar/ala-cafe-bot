# -*- coding: utf-8 -*-
"""
Ala Cafe Discord Bot - Master Kontrol & Karşılama Stüdyosu v3.0
"""
import os
import sys
import subprocess
import threading
import time
import sqlite3
import psutil
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "data", "bot.log")
BOT_SCRIPT = os.path.join(BASE_DIR, "bot.py")
TRANSCRIPTS_DIR = os.path.join(BASE_DIR, "data", "transcripts")
DB_PATH = os.path.join(BASE_DIR, "data", "cafe.db")

bot_process = None

class MasterStudioPanel(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("☕ Ala Cafe & Lounge — Master Kontrol & Stüdyo v3.0")
        self.geometry("980x720")
        self.minsize(850, 600)
        self.configure(bg="#181825")

        self.last_log_pos = 0
        self.is_running = False

        self.setup_styles()
        self.setup_ui()
        self.check_initial_process()
        self.start_log_monitor()
        self.start_process_poll()

    def setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        
        self.style.configure("TNotebook", background="#181825", borderwidth=0)
        self.style.configure(
            "TNotebook.Tab",
            background="#1e1e2e",
            foreground="#cdd6f4",
            padding=[14, 8],
            font=("Segoe UI", 10, "bold"),
            borderwidth=0
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", "#313244")],
            foreground=[("selected", "#fab387")]
        )

    def setup_ui(self):
        # Üst Başlık Barı
        top_bar = tk.Frame(self, bg="#1e1e2e", height=65, padx=20, pady=10)
        top_bar.pack(fill=tk.X, side=tk.TOP)

        title_box = tk.Frame(top_bar, bg="#1e1e2e")
        title_box.pack(side=tk.LEFT)

        tk.Label(
            title_box,
            text="☕ Ala Cafe & Lounge v3.0",
            font=("Segoe UI", 16, "bold"),
            fg="#fab387",
            bg="#1e1e2e"
        ).pack(anchor=tk.W)

        tk.Label(
            title_box,
            text="Müzik İstasyonu • Karşılama Stüdyosu • Nargile • Chat Arşivi",
            font=("Segoe UI", 9),
            fg="#a6adc8",
            bg="#1e1e2e"
        ).pack(anchor=tk.W)

        self.status_badge = tk.Label(
            top_bar,
            text="● KONTROL EDİLİYOR...",
            font=("Segoe UI", 10, "bold"),
            fg="#cdd6f4",
            bg="#313244",
            padx=14,
            pady=6
        )
        self.status_badge.pack(side=tk.RIGHT)

        # Hızlı Butonlar Barı
        btn_bar = tk.Frame(self, bg="#11111b", padx=20, pady=10)
        btn_bar.pack(fill=tk.X)

        self.btn_start = tk.Button(
            btn_bar, text="▶️ Botu Başlat", font=("Segoe UI", 10, "bold"),
            bg="#a6e3a1", fg="#11111b", activebackground="#94e2d5",
            padx=16, pady=5, relief=tk.FLAT, cursor="hand2",
            command=self.start_bot
        )
        self.btn_start.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_stop = tk.Button(
            btn_bar, text="⏹️ Botu Durdur", font=("Segoe UI", 10, "bold"),
            bg="#f38ba8", fg="#11111b", activebackground="#eba0ac",
            padx=16, pady=5, relief=tk.FLAT, cursor="hand2",
            command=self.stop_bot
        )
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_restart = tk.Button(
            btn_bar, text="🔄 Yeniden Başlat", font=("Segoe UI", 10, "bold"),
            bg="#89b4fa", fg="#11111b", activebackground="#b4befe",
            padx=16, pady=5, relief=tk.FLAT, cursor="hand2",
            command=self.restart_bot
        )
        self.btn_restart.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_open_folder = tk.Button(
            btn_bar, text="📁 Proje Klasörü", font=("Segoe UI", 9),
            bg="#313244", fg="#cdd6f4", activebackground="#45475a",
            padx=12, pady=5, relief=tk.FLAT, cursor="hand2",
            command=lambda: os.startfile(BASE_DIR)
        )
        self.btn_open_folder.pack(side=tk.RIGHT)

        # Sekmeli Alan (Notebook)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=12)

        # Sekme 1: Stüdyo (Mesaj ve Bot Yanıt Editörü)
        self.tab_studio = tk.Frame(self.notebook, bg="#181825")
        self.notebook.add(self.tab_studio, text="  🎛️ Bot & Karşılama Stüdyosu  ")
        self.setup_tab_studio()

        # Sekme 2: Canlı Loglar
        self.tab_logs = tk.Frame(self.notebook, bg="#181825")
        self.notebook.add(self.tab_logs, text="  📋 Canlı Log Akışı  ")
        self.setup_tab_logs()

        # Sekme 3: Chat Döküm Makinesi
        self.tab_transcripts = tk.Frame(self.notebook, bg="#181825")
        self.notebook.add(self.tab_transcripts, text="  📜 Chat Dökümleri  ")
        self.setup_tab_transcripts()

        # Sekme 4: Yönetim & VIP Kadrosu
        self.tab_vip = tk.Frame(self.notebook, bg="#181825")
        self.notebook.add(self.tab_vip, text="  👑 Yönetim & VIP  ")
        self.setup_tab_vip()

        # Sekme 5: Meşhur Nargileler
        self.tab_nargile = tk.Frame(self.notebook, bg="#181825")
        self.notebook.add(self.tab_nargile, text="  💨 Meşhur Nargileler  ")
        self.setup_tab_nargile()

    # --- SEKME 1: BOT & KARŞILAMA STÜDYOSU ---
    def setup_tab_studio(self):
        container = tk.Frame(self.tab_studio, bg="#181825", padx=20, pady=15)
        container.pack(fill=tk.BOTH, expand=True)

        # Başlık ve Açıklama
        hdr = tk.Frame(container, bg="#181825")
        hdr.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            hdr, text="Bot Karşılama, Cevap ve Durum Editörü",
            font=("Segoe UI", 12, "bold"), fg="#fab387", bg="#181825"
        ).pack(anchor=tk.W)

        tk.Label(
            hdr, text="Buradan değiştirdiğin her şey kod değiştirmeden anında veritabanına ve bota işlenir.",
            font=("Segoe UI", 9), fg="#a6adc8", bg="#181825"
        ).pack(anchor=tk.W)

        # 1. Hoş Geldin Başlığı
        f1 = tk.LabelFrame(container, text=" 1. Yeni Üye Karşılama Başlığı ", font=("Segoe UI", 10, "bold"), fg="#89b4fa", bg="#1e1e2e", padx=12, pady=8)
        f1.pack(fill=tk.X, pady=6)

        self.ent_welcome_title = tk.Entry(f1, font=("Segoe UI", 10), bg="#11111b", fg="#cdd6f4", insertbackground="#fab387", relief=tk.FLAT)
        self.ent_welcome_title.pack(fill=tk.X, pady=4)

        # 2. Hoş Geldin Mesajı (Açıklama)
        f2 = tk.LabelFrame(container, text=" 2. Yeni Üye Karşılama Mesajı (Açıklama Metni) ", font=("Segoe UI", 10, "bold"), fg="#89b4fa", bg="#1e1e2e", padx=12, pady=8)
        f2.pack(fill=tk.X, pady=6)

        tag_info = tk.Label(
            f2, text="Kullanabileceğin Değişkenler:  {kullanici} (Etiket)  •  {kullanici_adi}  •  {sunucu}  •  {uye_sayisi}",
            font=("Consolas", 8, "bold"), fg="#a6e3a1", bg="#1e1e2e"
        )
        tag_info.pack(anchor=tk.W, pady=(0, 4))

        self.txt_welcome_msg = scrolledtext.ScrolledText(
            f2, wrap=tk.WORD, height=4, font=("Segoe UI", 10),
            bg="#11111b", fg="#cdd6f4", insertbackground="#fab387", relief=tk.FLAT
        )
        self.txt_welcome_msg.pack(fill=tk.X, pady=4)

        # 3. Bot Durumu (Oynuyor/İzliyor)
        f3 = tk.LabelFrame(container, text=" 3. Bot Durum / Aktivite Metni (Discord Profilinin Altında Yazan) ", font=("Segoe UI", 10, "bold"), fg="#89b4fa", bg="#1e1e2e", padx=12, pady=8)
        f3.pack(fill=tk.X, pady=6)

        self.ent_bot_activity = tk.Entry(f3, font=("Segoe UI", 10), bg="#11111b", fg="#cdd6f4", insertbackground="#fab387", relief=tk.FLAT)
        self.ent_bot_activity.pack(fill=tk.X, pady=4)

        # 4. Varsayılan Ses Seviyesi
        f4 = tk.LabelFrame(container, text=" 4. Varsayılan Müzik Ses Seviyesi (%10 - %150) ", font=("Segoe UI", 10, "bold"), fg="#89b4fa", bg="#1e1e2e", padx=12, pady=8)
        f4.pack(fill=tk.X, pady=6)

        self.slider_vol = tk.Scale(f4, from_=10, to=150, orient=tk.HORIZONTAL, bg="#1e1e2e", fg="#cdd6f4", troughcolor="#11111b", activebackground="#fab387", highlightthickness=0)
        self.slider_vol.set(80)
        self.slider_vol.pack(fill=tk.X, pady=4)

        # Kaydet Butonu
        btn_save_frame = tk.Frame(container, bg="#181825", pady=10)
        btn_save_frame.pack(fill=tk.X)

        tk.Button(
            btn_save_frame, text="💾 TÜM DEĞİŞİKLİKLERİ KAYDET & BOTA YANSIT",
            font=("Segoe UI", 11, "bold"), bg="#a6e3a1", fg="#11111b",
            activebackground="#94e2d5", padx=20, pady=8, relief=tk.FLAT, cursor="hand2",
            command=self.save_studio_customizations
        ).pack(side=tk.LEFT)

        tk.Button(
            btn_save_frame, text="🔄 Ayarları Yenile",
            font=("Segoe UI", 9), bg="#313244", fg="#cdd6f4",
            padx=15, pady=8, relief=tk.FLAT, cursor="hand2",
            command=self.load_studio_customizations
        ).pack(side=tk.RIGHT)

        self.load_studio_customizations()

    def load_studio_customizations(self):
        if not os.path.exists(DB_PATH):
            return
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS bot_customizations (key TEXT PRIMARY KEY, value TEXT)")
            c.execute("SELECT key, value FROM bot_customizations")
            rows = c.fetchall()
            conn.close()

            data = {r[0]: r[1] for r in rows}

            self.ent_welcome_title.delete(0, tk.END)
            self.ent_welcome_title.insert(0, data.get("welcome_title", "☕ Ala Lounge'a Hoş Geldiniz!"))

            self.txt_welcome_msg.delete("1.0", tk.END)
            self.txt_welcome_msg.insert(tk.END, data.get("welcome_message", "Aramıza hoş geldin {kullanici}! Boş masalara geçebilirsin. Sunucumuz seninle {uye_sayisi} kişi oldu! 💨"))

            self.ent_bot_activity.delete(0, tk.END)
            self.ent_bot_activity.insert(0, data.get("bot_activity", "Ala Lounge & Nargile Masalarını 💨 | /oynat"))

            self.slider_vol.set(int(data.get("default_volume", 80)))
        except Exception as e:
            print("Stüdyo yükleme hatası:", e)

    def save_studio_customizations(self):
        title = self.ent_welcome_title.get().strip()
        msg = self.txt_welcome_msg.get("1.0", tk.END).strip()
        act = self.ent_bot_activity.get().strip()
        vol = str(self.slider_vol.get())

        if not title or not msg:
            messagebox.showwarning("Eksik Alan", "Başlık ve Mesaj alanları boş bırakılamaz.")
            return

        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS bot_customizations (key TEXT PRIMARY KEY, value TEXT)")
            items = [
                ("welcome_title", title),
                ("welcome_message", msg),
                ("bot_activity", act),
                ("default_volume", vol)
            ]
            for k, v in items:
                c.execute("INSERT INTO bot_customizations (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=?", (k, v, v))
            conn.commit()
            conn.close()

            messagebox.showinfo("Başarılı", "✅ Tüm ayarlar ve karşılama metinleri başarıyla kaydedildi!\nBot gelen yeni üyelere bu mesajla yanıt verecektir.")
            self.append_log("[STÜDYO] Karşılama mesajları ve bot ayarları güncellendi.\n", "SUCCESS")
        except Exception as e:
            messagebox.showerror("Hata", f"Kaydedilemedi: {e}")

    # --- SEKME 2: CANLI LOGLAR ---
    def setup_tab_logs(self):
        bar = tk.Frame(self.tab_logs, bg="#181825", pady=6)
        bar.pack(fill=tk.X)

        tk.Label(
            bar, text="Anlık Konsol ve Sistem Logları:",
            font=("Segoe UI", 10, "bold"), fg="#cdd6f4", bg="#181825"
        ).pack(side=tk.LEFT)

        tk.Button(
            bar, text="🧹 Logları Temizle", font=("Segoe UI", 8),
            bg="#313244", fg="#cdd6f4", activebackground="#45475a",
            padx=8, pady=2, relief=tk.FLAT, cursor="hand2",
            command=self.clear_logs
        ).pack(side=tk.RIGHT)

        self.log_text = scrolledtext.ScrolledText(
            self.tab_logs,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#11111b",
            fg="#cdd6f4",
            insertbackground="#fab387",
            selectbackground="#45475a",
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.log_text.tag_config("INFO", foreground="#89b4fa")
        self.log_text.tag_config("SUCCESS", foreground="#a6e3a1")
        self.log_text.tag_config("WARNING", foreground="#f9e2af")
        self.log_text.tag_config("ERROR", foreground="#f38ba8")

    # --- SEKME 3: CHAT DÖKÜMLERİ ---
    def setup_tab_transcripts(self):
        paned = tk.PanedWindow(self.tab_transcripts, orient=tk.HORIZONTAL, bg="#181825", sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left_frame = tk.Frame(paned, bg="#1e1e2e", width=280)
        paned.add(left_frame, minsize=220)

        bar = tk.Frame(left_frame, bg="#1e1e2e", padx=8, pady=6)
        bar.pack(fill=tk.X)

        tk.Label(bar, text="📁 Kayıtlı Dökümler:", font=("Segoe UI", 10, "bold"), fg="#cdd6f4", bg="#1e1e2e").pack(side=tk.LEFT)
        tk.Button(
            bar, text="🔄 Yenile", font=("Segoe UI", 8),
            bg="#313244", fg="#cdd6f4", relief=tk.FLAT, cursor="hand2",
            command=self.refresh_transcripts
        ).pack(side=tk.RIGHT)

        self.trans_listbox = tk.Listbox(
            left_frame, bg="#11111b", fg="#cdd6f4", font=("Consolas", 9),
            selectbackground="#fab387", selectforeground="#11111b", relief=tk.FLAT
        )
        self.trans_listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.trans_listbox.bind("<<ListboxSelect>>", self.on_transcript_select)

        right_frame = tk.Frame(paned, bg="#181825")
        paned.add(right_frame, minsize=450)

        right_bar = tk.Frame(right_frame, bg="#181825", pady=4)
        right_bar.pack(fill=tk.X)

        self.lbl_selected_doc = tk.Label(
            right_bar, text="Bir döküm dosyası seçin",
            font=("Segoe UI", 9, "italic"), fg="#a6adc8", bg="#181825"
        )
        self.lbl_selected_doc.pack(side=tk.LEFT)

        self.btn_open_notepad = tk.Button(
            right_bar, text="📝 Not Defterinde Aç", font=("Segoe UI", 8),
            bg="#89b4fa", fg="#11111b", relief=tk.FLAT, cursor="hand2",
            state=tk.DISABLED, command=self.open_current_in_notepad
        )
        self.btn_open_notepad.pack(side=tk.RIGHT)

        self.trans_text = scrolledtext.ScrolledText(
            right_frame, wrap=tk.WORD, font=("Consolas", 9),
            bg="#11111b", fg="#cdd6f4", relief=tk.FLAT, padx=10, pady=10
        )
        self.trans_text.pack(fill=tk.BOTH, expand=True)

        self.refresh_transcripts()

    def refresh_transcripts(self):
        self.trans_listbox.delete(0, tk.END)
        if os.path.exists(TRANSCRIPTS_DIR):
            files = sorted(os.listdir(TRANSCRIPTS_DIR), reverse=True)
            for f in files:
                if f.endswith(".txt"):
                    self.trans_listbox.insert(tk.END, f)

    def on_transcript_select(self, event):
        sel = self.trans_listbox.curselection()
        if not sel:
            return
        filename = self.trans_listbox.get(sel[0])
        filepath = os.path.join(TRANSCRIPTS_DIR, filename)
        self.lbl_selected_doc.config(text=f"Açık Dosya: {filename}", font=("Segoe UI", 9, "bold"))
        self.btn_open_notepad.config(state=tk.NORMAL)
        self.current_transcript_file = filepath

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            self.trans_text.delete("1.0", tk.END)
            self.trans_text.insert(tk.END, content)
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya okunamadı: {e}")

    def open_current_in_notepad(self):
        if hasattr(self, "current_transcript_file") and os.path.exists(self.current_transcript_file):
            os.startfile(self.current_transcript_file)

    # --- SEKME 4: YÖNETİM & VIP KADROSU ---
    def setup_tab_vip(self):
        add_frame = tk.LabelFrame(
            self.tab_vip, text=" ➕ Yönetim / VIP Üye Ekle ",
            font=("Segoe UI", 10, "bold"), fg="#fab387", bg="#1e1e2e", padx=15, pady=10
        )
        add_frame.pack(fill=tk.X, padx=10, pady=8)

        tk.Label(add_frame, text="Discord ID:", font=("Segoe UI", 9), fg="#cdd6f4", bg="#1e1e2e").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.ent_vip_id = tk.Entry(add_frame, font=("Segoe UI", 9), width=22, bg="#11111b", fg="#cdd6f4", relief=tk.FLAT)
        self.ent_vip_id.grid(row=0, column=1, padx=6, pady=4)

        tk.Label(add_frame, text="İsim / Rumuz:", font=("Segoe UI", 9), fg="#cdd6f4", bg="#1e1e2e").grid(row=0, column=2, sticky=tk.W, pady=4, padx=(10, 0))
        self.ent_vip_name = tk.Entry(add_frame, font=("Segoe UI", 9), width=20, bg="#11111b", fg="#cdd6f4", relief=tk.FLAT)
        self.ent_vip_name.grid(row=0, column=3, padx=6, pady=4)

        tk.Label(add_frame, text="Unvan / Rol:", font=("Segoe UI", 9), fg="#cdd6f4", bg="#1e1e2e").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.ent_vip_title = tk.Entry(add_frame, font=("Segoe UI", 9), width=22, bg="#11111b", fg="#cdd6f4", relief=tk.FLAT)
        self.ent_vip_title.grid(row=1, column=1, padx=6, pady=4)

        tk.Label(add_frame, text="Notlar:", font=("Segoe UI", 9), fg="#cdd6f4", bg="#1e1e2e").grid(row=1, column=2, sticky=tk.W, pady=4, padx=(10, 0))
        self.ent_vip_notes = tk.Entry(add_frame, font=("Segoe UI", 9), width=20, bg="#11111b", fg="#cdd6f4", relief=tk.FLAT)
        self.ent_vip_notes.grid(row=1, column=3, padx=6, pady=4)

        tk.Button(
            add_frame, text="Kaydet / Ekle", font=("Segoe UI", 9, "bold"),
            bg="#a6e3a1", fg="#11111b", padx=14, pady=3, relief=tk.FLAT, cursor="hand2",
            command=self.save_vip
        ).grid(row=1, column=4, padx=12, pady=4)

        tree_frame = tk.Frame(self.tab_vip, bg="#181825")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        cols = ("id", "name", "title", "notes", "added")
        self.tree_vip = ttk.Treeview(tree_frame, columns=cols, show="headings", height=8)
        self.tree_vip.heading("id", text="Discord ID")
        self.tree_vip.heading("name", text="İsim")
        self.tree_vip.heading("title", text="Unvan")
        self.tree_vip.heading("notes", text="Notlar")
        self.tree_vip.heading("added", text="Kayıt Tarihi")

        self.tree_vip.column("id", width=140)
        self.tree_vip.column("name", width=120)
        self.tree_vip.column("title", width=140)
        self.tree_vip.column("notes", width=180)
        self.tree_vip.column("added", width=120)

        self.tree_vip.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        btn_row = tk.Frame(self.tab_vip, bg="#181825")
        btn_row.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(
            btn_row, text="🗑️ Seçili Kişiyi Sil", font=("Segoe UI", 9),
            bg="#f38ba8", fg="#11111b", padx=12, pady=3, relief=tk.FLAT, cursor="hand2",
            command=self.delete_selected_vip
        ).pack(side=tk.LEFT)

        tk.Button(
            btn_row, text="🔄 Listeyi Yenile", font=("Segoe UI", 9),
            bg="#313244", fg="#cdd6f4", padx=12, pady=3, relief=tk.FLAT, cursor="hand2",
            command=self.refresh_vips
        ).pack(side=tk.RIGHT)

        self.refresh_vips()

    def refresh_vips(self):
        for item in self.tree_vip.get_children():
            self.tree_vip.delete(item)
        if not os.path.exists(DB_PATH):
            return
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS vip_members (user_id INTEGER PRIMARY KEY, name TEXT, title TEXT, notes TEXT, added_at TEXT)")
            c.execute("SELECT user_id, name, title, notes, added_at FROM vip_members ORDER BY added_at DESC")
            rows = c.fetchall()
            conn.close()
            for r in rows:
                self.tree_vip.insert("", tk.END, values=r)
        except Exception as e:
            print("VIP okuma hatası:", e)

    def save_vip(self):
        uid = self.ent_vip_id.get().strip()
        name = self.ent_vip_name.get().strip()
        title = self.ent_vip_title.get().strip()
        notes = self.ent_vip_notes.get().strip()

        if not uid or not name or not title:
            messagebox.showwarning("Eksik Bilgi", "Lütfen Discord ID, İsim ve Unvan alanlarını doldurun.")
            return

        try:
            user_id = int(uid)
        except ValueError:
            messagebox.showerror("Hata", "Discord ID yalnızca rakamlardan oluşmalıdır.")
            return

        now = time.strftime("%Y-%m-%d %H:%M")
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""
                INSERT INTO vip_members (user_id, name, title, notes, added_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET name=?, title=?, notes=?
            """, (user_id, name, title, notes, now, name, title, notes))
            conn.commit()
            conn.close()

            self.ent_vip_id.delete(0, tk.END)
            self.ent_vip_name.delete(0, tk.END)
            self.ent_vip_title.delete(0, tk.END)
            self.ent_vip_notes.delete(0, tk.END)
            self.refresh_vips()
            messagebox.showinfo("Başarılı", f"{name} ({title}) başarıyla listeye eklendi!")
        except Exception as e:
            messagebox.showerror("Hata", f"Veritabanı hatası: {e}")

    def delete_selected_vip(self):
        sel = self.tree_vip.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Lütfen silmek istediğiniz kişiyi seçin.")
            return
        vals = self.tree_vip.item(sel[0])["values"]
        user_id = vals[0]
        name = vals[1]

        if messagebox.askyesno("Onay", f"{name} adlı kişiyi listeden silmek istediğinize emin misiniz?"):
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("DELETE FROM vip_members WHERE user_id = ?", (user_id,))
                conn.commit()
                conn.close()
                self.refresh_vips()
            except Exception as e:
                messagebox.showerror("Hata", f"Silinemedi: {e}")

    # --- SEKME 5: MEŞHUR NARGİLELER ---
    def setup_tab_nargile(self):
        nargile_text = scrolledtext.ScrolledText(
            self.tab_nargile, wrap=tk.WORD, font=("Segoe UI", 10),
            bg="#11111b", fg="#cdd6f4", relief=tk.FLAT, padx=15, pady=15
        )
        nargile_text.pack(fill=tk.BOTH, expand=True)

        guide = (
            "================================================================================\n"
            "   💨 ALA CAFE & LOUNGE — MEŞHUR NARGİLE VE TÜTÜN REÇETELERİ\n"
            "================================================================================\n\n"
            "🌟 1. ALA ÖZEL İMZA KARIŞIMLARI:\n"
            "--------------------------------------------------------------------------------\n"
            "• Ala Special (Kral Karışım):\n"
            "  - Karışım: Love 66 (%40) + Lady Killer (%30) + Mango (%20) + Hafif Buz (%10)\n"
            "  - Tat: Meyvemsi, tatlı, yoğun beyaz duman.\n"
            "  - Lüle/Köz: Phunnel Lüle + Lotus HMD + 3 adet 26mm hindistan cevizi közü.\n"
            "  - Usta Tüyosu: Tütünleri ezmeden havalandırarak harmanlayın, folyoya değdirmeyin.\n\n"
            "• Bosphorus Night (Boğaz Esintisi):\n"
            "  - Karışım: Yaban Mersini (%50) + Guava (%30) + Taze Nane (%20)\n"
            "  - Tat: Mayhoş orman meyveleri ve serinletici ferahlık.\n\n"
            "• Havana Sunset (Tropik Günbatımı):\n"
            "  - Karışım: Ananas (%40) + Maracuja (%35) + Çarkıfelek (%25)\n"
            "  - Tat: Yoğun ekşi-tatlı tropikal patlama.\n\n"
            "🍎 2. GELENEKSEL & ESNAF KLASİKLERİ:\n"
            "--------------------------------------------------------------------------------\n"
            "• Nostalji Hakiki Çift Elma & Nane:\n"
            "  - Karışım: Nakhla/Al Fakher Çift Elma (%80) + Nane Sakız (%20)\n"
            "  - Tat: Tok anason vuruşu, klasik kahveci nargilesi.\n"
            "  - Lüle: Geleneksel toprak lüle + hakiki deri marpuç.\n\n"
            "• Efsane Siyah Üzüm & Nane:\n"
            "  - Karışım: Siyah Üzüm (%70) + Nane (%30)\n\n"
            "🍰 3. TATLI & KREMSİ SEÇENEKLER:\n"
            "--------------------------------------------------------------------------------\n"
            "• Pişmiş Şeftali & Bisküvi Şöleni (%50 Pişmiş Şeftali + %30 Bisküvi + %20 Vanilya)\n"
            "• Karamel Macchiato (%40 Kahve + %40 Karamel + %20 Süt)\n\n"
            "🔥 4. KUSURSUZ NARGİLE İÇİN 4 ALTIN KURAL:\n"
            "--------------------------------------------------------------------------------\n"
            "1. Tütünü lüleye bastırmayın, havalandırarak bırakın.\n"
            "2. Tütün en az 2 mm folyodan/metalden aşağıda kalsın.\n"
            "3. Közleri 20 dakikada bir kenarlara çevirin.\n"
            "4. Her seans sonrası ser ve şişeyi fırçalayın.\n"
        )
        nargile_text.insert(tk.END, guide)
        nargile_text.config(state=tk.DISABLED)

    # --- SÜREÇ YÖNETİMİ & LOG İZLEYİCİ ---
    def check_initial_process(self):
        try:
            for p in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmd = p.info.get('cmdline') or []
                    if any('bot.py' in str(arg) for arg in cmd):
                        self.is_running = True
                        self.update_status(True)
                        return
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass
        self.update_status(False)

    def start_process_poll(self):
        def poll():
            while True:
                time.sleep(2)
                running = False
                for p in psutil.process_iter(['pid', 'cmdline']):
                    try:
                        cmd = p.info.get('cmdline') or []
                        if any('bot.py' in str(arg) for arg in cmd):
                            running = True
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                if running != self.is_running:
                    self.after(0, self.update_status, running)

        t = threading.Thread(target=poll, daemon=True)
        t.start()

    def update_status(self, running):
        self.is_running = running
        if running:
            self.status_badge.config(text="● ÇEVRİMİÇİ (ÇALIŞIYOR)", bg="#2d4f3b", fg="#a6e3a1")
            self.btn_start.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
        else:
            self.status_badge.config(text="● KAPALI (DURDURULDU)", bg="#49242d", fg="#f38ba8")
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)

    def start_bot(self):
        global bot_process
        if self.is_running:
            return
        try:
            py_exe = sys.executable.replace("pythonw.exe", "python.exe")
            bot_process = subprocess.Popen(
                [py_exe, BOT_SCRIPT],
                cwd=BASE_DIR,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            self.update_status(True)
            self.append_log("[PANEL] Bot v3.0 süreci başlatıldı.\n", "SUCCESS")
        except Exception as e:
            messagebox.showerror("Hata", f"Bot başlatılamadı: {e}")

    def stop_bot(self):
        global bot_process
        try:
            for p in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmd = p.info.get('cmdline') or []
                    if any('bot.py' in str(arg) for arg in cmd):
                        p.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            bot_process = None
            self.update_status(False)
            self.append_log("[PANEL] Bot süreci durduruldu.\n", "WARNING")
        except Exception as e:
            messagebox.showerror("Hata", f"Bot durdurulamadı: {e}")

    def restart_bot(self):
        self.append_log("[PANEL] Bot yeniden başlatılıyor...\n", "INFO")
        self.stop_bot()
        time.sleep(1.5)
        self.start_bot()

    def clear_logs(self):
        self.log_text.delete("1.0", tk.END)
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, "w", encoding="utf-8") as f:
                    f.write("")
                self.last_log_pos = 0
            except Exception:
                pass

    def append_log(self, text, tag="INFO"):
        self.log_text.insert(tk.END, text, tag)
        self.log_text.see(tk.END)

    def start_log_monitor(self):
        def monitor():
            while True:
                if os.path.exists(LOG_FILE):
                    try:
                        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                            f.seek(self.last_log_pos)
                            new_data = f.read()
                            if new_data:
                                self.last_log_pos = f.tell()
                                self.after(0, self.process_new_logs, new_data)
                    except Exception:
                        pass
                time.sleep(1)

        t = threading.Thread(target=monitor, daemon=True)
        t.start()

    def process_new_logs(self, text):
        lines = text.splitlines(keepends=True)
        for line in lines:
            tag = "INFO"
            if "ERROR" in line or "Exception" in line or "Traceback" in line:
                tag = "ERROR"
            elif "WARNING" in line:
                tag = "WARNING"
            elif "senkronize edildi" in line or "hazırlandı" in line or "başarıyla" in line:
                tag = "SUCCESS"
            self.append_log(line, tag)

if __name__ == "__main__":
    app = MasterStudioPanel()
    app.mainloop()

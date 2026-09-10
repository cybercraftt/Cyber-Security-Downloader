import os
import sys
import time
import datetime
import threading
import ssl
import urllib.request
import urllib.parse
import hashlib
import json
import re
import subprocess
import webbrowser
import customtkinter as ctk
from tkinter import filedialog, messagebox

if sys.platform == "win32":
    import winsound
    import ctypes

ctk.set_appearance_mode("Dark")

UTILITIES = {
    "Dr.Web CureIt!": {
        "url": "https://free.drweb.ru/download+cureit+free/",
        "download_url": "https://free.drweb.ru/download+cureit/gr/?lng=ru",
        "referer": "https://free.drweb.ru/download+cureit+free/",
        "default_filename": "cureit.exe",
        "description": "Автономный антивирусный сканер"
    },
    "AdwCleaner": {
        "url": "https://www.malwarebytes.com/adwcleaner",
        "download_url": "https://adwcleaner.malwarebytes.com/adwcleaner?channel=release",
        "referer": "https://www.malwarebytes.com/",
        "default_filename": "adwcleaner.exe",
        "description": "Удаление Adware, PUP и браузерных плагинов"
    }
}

DEFAULT_SETTINGS = {
    "last_utility": "Dr.Web CureIt!",
    "downloads_folder": "Downloads"
}

def get_base_dir():
    """Гарантированно возвращает папку, где расположен сам .exe или .py файл."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_resource_path(relative_path):
    """Получение пути к временным ресурсам (звуки, иконки) для PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = get_base_dir()
    return os.path.join(base_path, relative_path)

def parse_content_disposition(header):
    if not header:
        return None
    utf8_match = re.search(r"filename\*\s*=\s*UTF-8''([^;]+)", header, re.IGNORECASE)
    if utf8_match:
        return urllib.parse.unquote(utf8_match.group(1))
    std_match = re.search(r'filename\s*=\s*"?([^";]+)"?', header, re.IGNORECASE)
    if std_match:
        return std_match.group(1)
    return None

class ConfigManager:
    """Управление внешним файлом настроек settings.json рядом с .exe"""
    def __init__(self, filename="settings.json"):
        self.filepath = os.path.join(get_base_dir(), filename)
        self.settings = self.load_settings()

    def load_settings(self):
        if not os.path.exists(self.filepath):
            self.save_settings(DEFAULT_SETTINGS)
            return DEFAULT_SETTINGS.copy()
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, value in DEFAULT_SETTINGS.items():
                    data.setdefault(key, value)
                return data
        except Exception:
            self.save_settings(DEFAULT_SETTINGS)
            return DEFAULT_SETTINGS.copy()

    def save_settings(self, data=None):
        if data is not None:
            self.settings = data
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения settings.json: {e}")

    def get(self, key):
        return self.settings.get(key, DEFAULT_SETTINGS.get(key))

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

class CyberDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        if sys.platform == "win32":
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("CyberCraft.UtilityDownloader.App.2.3")
            except Exception:
                pass

        self.title("Cyber Security Downloader")
        self.downloading = False
        self.cancel_requested = False
        self.downloaded_file_path = None
        self.remote_file_size = 0
        self.is_update_available = False

        # Менеджер настроек
        self.config = ConfigManager("settings.json")
        self.selected_utility = self.config.get("last_utility")

        # Цветовая гамма
        self.CARD_BG = "#14151C"
        self.CARD_BORDER = "#232533"
        self.ACCENT_COLOR = "#6366F1"
        self.ACCENT_HOVER = "#4F46E5"
        self.UPDATE_COLOR = "#10B981"
        self.UPDATE_HOVER = "#059669"
        self.CANCEL_COLOR = "#EF4444"
        self.CANCEL_HOVER = "#DC2626"

        icon_path = get_resource_path("icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.center_window(460, 560)
        self.setup_ui()

        # Инициализация пути сохранения из настроек
        saved_folder = self.config.get("downloads_folder")
        if not os.path.isabs(saved_folder):
            target_dir = os.path.join(get_base_dir(), saved_folder)
        else:
            target_dir = saved_folder

        os.makedirs(target_dir, exist_ok=True)
        self.path_entry.configure(state="normal")
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, target_dir)
        self.path_entry.configure(state="readonly")

        self.check_existing_file()
        self.check_remote_updates_async()

    def center_window(self, width, height):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def setup_ui(self):
        self.configure(fg_color="#0B0C10")

        # Выбор утилиты
        selector_frame = ctk.CTkFrame(self, fg_color="transparent")
        selector_frame.pack(fill="x", padx=14, pady=(12, 4))

        self.util_selector = ctk.CTkSegmentedButton(
            selector_frame,
            values=list(UTILITIES.keys()),
            selected_color=self.ACCENT_COLOR,
            unselected_color="#1E202E",
            unselected_hover_color="#282A3D",
            text_color="#F3F4F6",
            font=("Segoe UI", 11, "bold"),
            command=self.on_utility_change
        )
        self.util_selector.set(self.selected_utility)
        self.util_selector.pack(fill="x")

        # Карточка статуса
        status_card = ctk.CTkFrame(
            self, fg_color=self.CARD_BG, border_width=1, border_color=self.CARD_BORDER, corner_radius=12
        )
        status_card.pack(fill="x", padx=14, pady=(4, 6))

        status_box = ctk.CTkFrame(status_card, fg_color="#1E202E", corner_radius=16)
        status_box.pack(pady=(8, 2), padx=10)

        self.status_badge = ctk.CTkLabel(
            status_box, text="● Проверка состояния...", font=("Segoe UI", 11, "bold"), text_color="#9CA3AF"
        )
        self.status_badge.pack(padx=12, pady=3)

        self.size_label = ctk.CTkLabel(
            status_card, text="Размер: Определение...", font=("Segoe UI", 20, "bold"), text_color="#F3F4F6"
        )
        self.size_label.pack(pady=0)

        self.info_label = ctk.CTkLabel(
            status_card, text=UTILITIES[self.selected_utility]["description"], font=("Segoe UI", 10, "bold"), text_color="#6B7280"
        )
        self.info_label.pack(pady=(1, 6))

        # Настройка папки
        settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        settings_frame.pack(padx=14, fill="x", pady=0)

        path_card = ctk.CTkFrame(
            settings_frame, fg_color=self.CARD_BG, border_width=1, border_color=self.CARD_BORDER, corner_radius=10
        )
        path_card.pack(fill="x", pady=2, ipady=2, ipadx=6)

        self.path_label = ctk.CTkLabel(
            path_card, text="Папка для сохранения:", font=("Segoe UI", 11, "bold"), text_color="#E5E7EB"
        )
        self.path_label.pack(anchor="w", padx=6, pady=(2, 0))

        self.use_script_dir_var = ctk.BooleanVar(value=True)
        self.same_folder_checkbox = ctk.CTkSwitch(
            path_card,
            text="Использовать папку Downloads рядом с программой",
            variable=self.use_script_dir_var,
            font=("Segoe UI", 10),
            progress_color=self.ACCENT_COLOR,
            text_color="#9CA3AF",
            command=self.toggle_path_mode
        )
        self.same_folder_checkbox.pack(anchor="w", padx=6, pady=(1, 4))

        self.path_input_frame = ctk.CTkFrame(path_card, fg_color="transparent")
        self.path_input_frame.pack(fill="x", padx=6, pady=(0, 2))

        self.path_entry = ctk.CTkEntry(
            self.path_input_frame,
            height=26,
            font=("Segoe UI", 10),
            fg_color="#0B0C10",
            border_color=self.CARD_BORDER,
            text_color="#F3F4F6"
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.browse_button = ctk.CTkButton(
            self.path_input_frame,
            text="Обзор...",
            width=60,
            height=26,
            font=("Segoe UI", 10),
            fg_color="#1E202E",
            hover_color="#282A3D",
            text_color="#9CA3AF",
            border_width=1,
            border_color="#282A3D",
            state="disabled",
            command=self.browse_folder
        )
        self.browse_button.pack(side="right")

        # Прогресс-бар
        self.progress_bar = ctk.CTkProgressBar(
            self, height=8, fg_color="#1E202E", progress_color=self.ACCENT_COLOR
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(padx=14, pady=(8, 4), fill="x")

        # Кнопки действия
        btn_container = ctk.CTkFrame(self, fg_color="transparent")
        btn_container.pack(pady=2, padx=14, fill="x")

        self.download_button = ctk.CTkButton(
            btn_container,
            text=f"Скачать {self.selected_utility}",
            font=("Segoe UI", 12, "bold"),
            height=34,
            corner_radius=8,
            fg_color=self.ACCENT_COLOR,
            hover_color=self.ACCENT_HOVER,
            command=self.handle_download_click
        )
        self.download_button.pack(expand=True, fill="x", pady=(0, 4))

        action_row = ctk.CTkFrame(btn_container, fg_color="transparent")
        action_row.pack(fill="x")

        self.action_button = ctk.CTkButton(
            action_row,
            text="Запустить утилиту",
            font=("Segoe UI", 11, "bold"),
            height=28,
            corner_radius=6,
            fg_color="#1E202E",
            hover_color="#282A3D",
            text_color="#9CA3AF",
            border_width=1,
            border_color="#282A3D",
            state="disabled",
            command=self.run_downloaded_file
        )
        self.action_button.pack(side="left", expand=True, fill="x", padx=(0, 2))

        self.open_folder_button = ctk.CTkButton(
            action_row,
            text="Открыть папку",
            font=("Segoe UI", 11, "bold"),
            height=28,
            width=110,
            corner_radius=6,
            fg_color="#1E202E",
            hover_color="#282A3D",
            text_color="#9CA3AF",
            border_width=1,
            border_color="#282A3D",
            command=self.open_download_folder
        )
        self.open_folder_button.pack(side="right", padx=(2, 0))

        # Подвал
        links_frame = ctk.CTkFrame(self, fg_color="transparent")
        links_frame.pack(side="bottom", pady=8)

        ctk.CTkLabel(links_frame, text="Поддержка проекта", font=("Segoe UI", 9), text_color="#4B5563").pack(pady=(0, 2))

        btn_box = ctk.CTkFrame(links_frame, fg_color="transparent")
        btn_box.pack()

        yt_btn = ctk.CTkButton(
            btn_box, text="YouTube", font=("Segoe UI", 10, "bold"), width=85, height=24, corner_radius=6,
            fg_color="#1E202E", hover_color="#282A3D", text_color="#EF4444", border_width=1, border_color="#282A3D",
            command=lambda: webbrowser.open("https://www.youtube.com/channel/UCcGfKjP4XdfkLokNgVOIAyA")
        )
        yt_btn.pack(side="left", padx=2)

        tg_btn = ctk.CTkButton(
            btn_box, text="Telegram", font=("Segoe UI", 10, "bold"), width=85, height=24, corner_radius=6,
            fg_color="#1E202E", hover_color="#282A3D", text_color="#38BDF8", border_width=1, border_color="#282A3D",
            command=lambda: webbrowser.open("https://t.me/CyberCraftLab")
        )
        tg_btn.pack(side="left", padx=2)

        boosty_btn = ctk.CTkButton(
            btn_box, text="Boosty", font=("Segoe UI", 10, "bold"), width=85, height=24, corner_radius=6,
            fg_color="#1E202E", hover_color="#282A3D", text_color="#FB923C", border_width=1, border_color="#282A3D",
            command=lambda: webbrowser.open("https://boosty.to/cyber_craft")
        )
        boosty_btn.pack(side="left", padx=2)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def check_existing_file(self):
        util_info = UTILITIES[self.selected_utility]
        target_dir = self.path_entry.get()
        
        found_file = None
        if os.path.exists(target_dir):
            if self.selected_utility == "Dr.Web CureIt!":
                for f in os.listdir(target_dir):
                    if f.lower().endswith(".exe") and ("cureit" in f.lower() or f.lower().startswith("drweb")):
                        found_file = os.path.join(target_dir, f)
                        break
            else:
                default_path = os.path.join(target_dir, util_info["default_filename"])
                if os.path.exists(default_path):
                    found_file = default_path

        if found_file and os.path.exists(found_file):
            self.downloaded_file_path = found_file
            file_mtime = os.path.getmtime(found_file)
            time_str = datetime.datetime.fromtimestamp(file_mtime).strftime("%d.%m %H:%M")
            file_size_mb = os.path.getsize(found_file) / (1024 * 1024)

            self.status_badge.configure(text=f"● Локальный файл от {time_str}", text_color="#60A5FA")
            self.size_label.configure(text=f"Локально: {file_size_mb:.2f} МБ")
            self.info_label.configure(text="Проверка свежих баз на сервере...", text_color="#9CA3AF")
            self.download_button.configure(
                text=f"Скачать заново",
                fg_color=self.ACCENT_COLOR,
                hover_color=self.ACCENT_HOVER
            )
            self.action_button.configure(state="normal")
            self.progress_bar.set(1.0)
        else:
            self.downloaded_file_path = None
            self.is_update_available = False
            self.status_badge.configure(text="● Файл не найден", text_color="#9CA3AF")
            self.size_label.configure(text="Размер: Определение...")
            self.info_label.configure(text=util_info["description"], text_color="#6B7280")
            self.download_button.configure(
                text=f"Скачать {self.selected_utility}",
                fg_color=self.ACCENT_COLOR,
                hover_color=self.ACCENT_HOVER
            )
            self.action_button.configure(state="disabled")
            self.progress_bar.set(0)

    def check_remote_updates_async(self):
        threading.Thread(target=self._check_remote_worker, daemon=True).start()

    def _check_remote_worker(self):
        util_info = UTILITIES[self.selected_utility]
        try:
            ctx = ssl.create_default_context()
            req = urllib.request.Request(
                util_info["download_url"],
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                    'Referer': util_info["referer"]
                },
                method='HEAD'
            )
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                length = resp.info().get('Content-Length')
                if length:
                    remote_bytes = int(length)
                    size_mb = remote_bytes / (1024 * 1024)
                    self.remote_file_size = size_mb

                    update_needed = False
                    if self.downloaded_file_path and os.path.exists(self.downloaded_file_path):
                        local_bytes = os.path.getsize(self.downloaded_file_path)
                        file_mtime = os.path.getmtime(self.downloaded_file_path)
                        age_hours = (time.time() - file_mtime) / 3600
                        # Если размер отличается более чем на 50 КБ или файл старше 20 часов
                        if abs(local_bytes - remote_bytes) > 50 * 1024 or age_hours > 20:
                            update_needed = True

                    self.after(0, lambda: self._apply_update_check_results(size_mb, update_needed))
        except Exception:
            pass

    def _apply_update_check_results(self, size_mb, update_needed):
        if self.downloading:
            return

        if self.downloaded_file_path and os.path.exists(self.downloaded_file_path):
            if update_needed:
                self.is_update_available = True
                self.status_badge.configure(text="● ДОСТУПНА НОВАЯ ВЕРСИЯ!", text_color="#10B981")
                self.info_label.configure(text=f"На сервере появилась свежая база ({size_mb:.1f} МБ)", text_color="#10B981")
                self.download_button.configure(
                    text=f"Обновить {self.selected_utility}",
                    fg_color=self.UPDATE_COLOR,
                    hover_color=self.UPDATE_HOVER
                )
            else:
                self.is_update_available = False
                self.status_badge.configure(text="● Установлена актуальная версия", text_color="#3B82F6")
                self.info_label.configure(text="Ваша версия совпадает с последней базой на сервере", text_color="#3B82F6")
                self.download_button.configure(
                    text="Перекачать файл",
                    fg_color=self.ACCENT_COLOR,
                    hover_color=self.ACCENT_HOVER
                )
        else:
            self.size_label.configure(text=f"Размер: ~{size_mb:.1f} МБ")

    def on_utility_change(self, choice):
        if self.downloading:
            self.util_selector.set(self.selected_utility)
            return
        self.selected_utility = choice
        self.config.set("last_utility", choice)
        self.check_existing_file()
        self.check_remote_updates_async()

    def play_sound(self, sound_type="success"):
        if sys.platform == "win32":
            if sound_type == "success":
                sound_path = get_resource_path("alert.wav")
                if os.path.exists(sound_path):
                    try:
                        winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                        return
                    except Exception:
                        pass
                winsound.PlaySound("SystemNotification", winsound.SND_ALIAS | winsound.SND_ASYNC)
            else:
                winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC)

    def toggle_path_mode(self):
        if self.use_script_dir_var.get():
            downloads_dir = os.path.join(get_base_dir(), "Downloads")
            os.makedirs(downloads_dir, exist_ok=True)
            self.path_entry.configure(state="normal")
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, downloads_dir)
            self.path_entry.configure(state="readonly")
            self.browse_button.configure(state="disabled")
            self.config.set("downloads_folder", "Downloads")
        else:
            self.browse_button.configure(state="normal")
        self.check_existing_file()
        self.check_remote_updates_async()

    def browse_folder(self):
        selected_directory = filedialog.askdirectory(
            title="Выберите папку для сохранения",
            initialdir=self.path_entry.get()
        )
        if selected_directory:
            self.path_entry.configure(state="normal")
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, selected_directory)
            self.path_entry.configure(state="readonly")
            self.config.set("downloads_folder", selected_directory)
            self.check_existing_file()
            self.check_remote_updates_async()

    def handle_download_click(self):
        if self.downloading:
            self.cancel_requested = True
            self.download_button.configure(text="Отмена...", state="disabled")
        else:
            self.start_download_thread()

    def start_download_thread(self):
        self.downloading = True
        self.cancel_requested = False
        
        self.download_button.configure(
            text="Отменить загрузку",
            fg_color=self.CANCEL_COLOR,
            hover_color=self.CANCEL_HOVER,
            state="normal"
        )
        self.action_button.configure(state="disabled")
        self.browse_button.configure(state="disabled")
        self.same_folder_checkbox.configure(state="disabled")
        self.util_selector.configure(state="disabled")

        self.status_badge.configure(text="● Соединение с сервером...", text_color="#06B6D4")
        self.info_label.configure(text="Подключение к серверу...", text_color="#06B6D4")

        threading.Thread(target=self.download_process, daemon=True).start()

    def download_process(self):
        util_info = UTILITIES[self.selected_utility]
        url = util_info["download_url"]
        target_dir = self.path_entry.get()
        os.makedirs(target_dir, exist_ok=True)

        save_path = os.path.join(target_dir, util_info["default_filename"])
        temp_save_path = save_path + ".tmp"

        ctx = ssl.create_default_context()

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': util_info["referer"],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }

        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                if response.status != 200:
                    raise Exception(f"Сервер вернул код {response.status}")

                cd_header = response.info().get('Content-Disposition')
                parsed_filename = parse_content_disposition(cd_header)
                if parsed_filename:
                    save_path = os.path.join(target_dir, parsed_filename)
                    temp_save_path = save_path + ".tmp"

                total_size = int(response.info().get('Content-Length', 0))
                downloaded = 0
                block_size = 1024 * 64
                start_time = time.time()
                sha256_hash = hashlib.sha256()

                with open(temp_save_path, 'wb') as out_file:
                    while True:
                        if self.cancel_requested:
                            raise Exception("Загрузка отменена пользователем")

                        buffer = response.read(block_size)
                        if not buffer:
                            break

                        downloaded += len(buffer)
                        sha256_hash.update(buffer)
                        out_file.write(buffer)

                        dl_mb = downloaded / (1024 * 1024)
                        tot_mb = total_size / (1024 * 1024) if total_size > 0 else 0
                        progress = downloaded / total_size if total_size > 0 else 0

                        elapsed = time.time() - start_time
                        speed = (downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                        eta_sec = int((total_size - downloaded) / (speed * 1024 * 1024)) if speed > 0 and total_size > 0 else 0

                        self.after(0, self.update_download_status, dl_mb, tot_mb, progress, speed, eta_sec)

                if downloaded < 100 * 1024:
                    raise Exception("Файл слишком мал для исполняемого модуля")

                with open(temp_save_path, 'rb') as check_file:
                    header_bytes = check_file.read(2)
                    if header_bytes != b'MZ':
                        raise Exception("Скачанный файл не является правильным исполняемым файлом Windows (.exe)")

            if os.path.exists(save_path):
                os.remove(save_path)
            os.rename(temp_save_path, save_path)

            final_hash = sha256_hash.hexdigest()
            print(f"[{self.selected_utility}] SHA-256: {final_hash}")

            self.downloaded_file_path = save_path
            self.after(0, self.on_download_complete)

        except Exception as e:
            if os.path.exists(temp_save_path):
                try:
                    os.remove(temp_save_path)
                except Exception:
                    pass
            self.after(0, self.on_download_error, str(e))

    def update_download_status(self, dl_mb, tot_mb, progress, speed, eta_sec):
        self.progress_bar.set(progress)
        self.status_badge.configure(text="● Загрузка новой версии...", text_color="#06B6D4")
        
        if tot_mb > 0:
            self.size_label.configure(text=f"{dl_mb:.1f} МБ / {tot_mb:.1f} МБ")
            self.info_label.configure(text=f"{speed:.2f} МБ/с • осталось ~{eta_sec} сек", text_color="#06B6D4")
        else:
            self.size_label.configure(text=f"{dl_mb:.2f} МБ")
            self.info_label.configure(text=f"Скорость: {speed:.2f} МБ/с", text_color="#06B6D4")

    def on_download_complete(self):
        self.downloading = False
        self.is_update_available = False
        self.play_sound("success")
        self.status_badge.configure(text="● Установлена актуальная версия", text_color="#10B981")
        self.info_label.configure(text="База данных вирусных сигнатур обновлена", text_color="#10B981")
        
        self.download_button.configure(
            text="Перекачать файл",
            fg_color=self.ACCENT_COLOR,
            hover_color=self.ACCENT_HOVER,
            state="normal"
        )
        self.action_button.configure(state="normal")
        self.same_folder_checkbox.configure(state="normal")
        self.util_selector.configure(state="normal")
        if not self.use_script_dir_var.get():
            self.browse_button.configure(state="normal")

    def on_download_error(self, err_msg):
        self.downloading = False
        self.download_button.configure(
            text=f"Скачать {self.selected_utility}",
            fg_color=self.ACCENT_COLOR,
            hover_color=self.ACCENT_HOVER,
            state="normal"
        )
        self.same_folder_checkbox.configure(state="normal")
        self.util_selector.configure(state="normal")
        if not self.use_script_dir_var.get():
            self.browse_button.configure(state="normal")

        if "отменена" in err_msg.lower():
            self.play_sound("error")
            self.status_badge.configure(text="● Отменено пользователем", text_color="#9CA3AF")
            self.info_label.configure(text="Загрузка остановлена", text_color="#9CA3AF")
            self.progress_bar.set(0)
        else:
            self.play_sound("error")
            self.status_badge.configure(text="● Ошибка загрузки", text_color="#EF4444")
            self.info_label.configure(text="Не удалось обновить утилиту", text_color="#EF4444")
            messagebox.showerror("Ошибка загрузки", f"Не удалось безопасно скачать файл:\n{err_msg}")

    def run_downloaded_file(self):
        if self.downloaded_file_path and os.path.exists(self.downloaded_file_path):
            try:
                os.startfile(self.downloaded_file_path)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось запустить файл:\n{e}")

    def open_download_folder(self):
        target_dir = self.path_entry.get()
        if os.path.exists(target_dir):
            if sys.platform == "win32":
                os.startfile(target_dir)
            else:
                subprocess.Popen(["xdg-open", target_dir])

    def on_closing(self):
        if self.downloading:
            self.cancel_requested = True
        self.destroy()

if __name__ == "__main__":
    app = CyberDownloaderApp()
    app.mainloop()
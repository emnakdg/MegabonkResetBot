import tkinter as tk
from tkinter import messagebox, scrolledtext
import customtkinter as ctk
import threading
import time
import re
import json
import winsound
import cv2
import numpy as np
import pyautogui
import keyboard
import os
import sys
import subprocess
import tempfile
import urllib.request
import urllib.error
from PIL import Image, ImageTk

try:
    import pytesseract
except ImportError:
    pass

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

VERSION = "1.0.0"
GITHUB_REPO = "emnakdg/MegabonkResetBot"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")


def check_for_updates(callback):
    """Arka planda güncelleme kontrolü yapar, sonucu callback'e iletir."""
    try:
        req = urllib.request.Request(GITHUB_API_URL, headers={"User-Agent": "MegabonkBot"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        latest_tag = data.get("tag_name", "").lstrip("v")
        download_url = None
        for asset in data.get("assets", []):
            if asset["name"].endswith(".exe"):
                download_url = asset["browser_download_url"]
                break
        if latest_tag and latest_tag != VERSION and download_url:
            callback(latest_tag, download_url)
    except Exception:
        pass


def apply_update(download_url, on_progress=None):
    """Yeni exe'yi indirir, bat ile değiştirir. Kullanıcı uygulamayı kapatıp açınca güncelleme tamamlanır."""
    try:
        current_exe = sys.executable
        exe_dir = os.path.dirname(current_exe)
        tmp_exe = os.path.join(exe_dir, "_megabonk_update.exe")

        urllib.request.urlretrieve(download_url, tmp_exe)

        # Bat sadece değiştirme yapar, yeniden başlatmaz — env inheritance sorununu önler
        bat = f"""@echo off
timeout /t 2 /nobreak >nul
move /y "{tmp_exe}" "{current_exe}"
del "%~f0"
"""
        bat_path = os.path.join(exe_dir, "_megabonk_update.bat")
        with open(bat_path, "w") as f:
            f.write(bat)

        subprocess.Popen(
            ["cmd", "/c", bat_path],
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
        )
        if on_progress:
            on_progress()
    except Exception as e:
        messagebox.showerror("Güncelleme Hatası", f"Güncelleme sırasında hata oluştu:\n{e}")


class MegabonkBot:
    def __init__(self, root):
        self.root = root
        self.root.title("Megabonk Auto R Bot")
        self.root.geometry("420x520")
        self.root.resizable(False, False)

        self.running = False
        self.reroll_count = 0
        self.start_time = 0
        self.debug_win = None
        self.debug_img_label = None

        # Başlık
        ctk.CTkLabel(root, text="Megabonk Auto R Bot", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(15, 2))
        ctk.CTkLabel(root, text=f"v{VERSION}", font=ctk.CTkFont(size=11), text_color="gray").pack(pady=(0, 5))

        # Tesseract Yolu
        tess_frame = ctk.CTkFrame(root)
        tess_frame.pack(fill="x", padx=15, pady=(5, 0))
        ctk.CTkLabel(tess_frame, text="Tesseract Yolu", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(8, 2))
        self.tess_path_var = tk.StringVar(value=r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        ctk.CTkEntry(tess_frame, textvariable=self.tess_path_var, width=380, height=32).pack(padx=10, pady=(0, 10))

        # Hedef Ayarları Kartı
        settings_frame = ctk.CTkFrame(root)
        settings_frame.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(settings_frame, text="Hedef Ayarları", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=(8, 4), sticky="w")

        labels = ["Minimum Moais Sayısı", "Minimum Shady Guy Sayısı", "Minimum Microwaves Sayısı", "ESC Gecikmesi (saniye)"]
        self.moais_var = tk.IntVar(value=3)
        self.shady_var = tk.IntVar(value=1)
        self.micro_var = tk.IntVar(value=0)
        self.delay_var = tk.DoubleVar(value=0.1)
        vars_ = [self.moais_var, self.shady_var, self.micro_var, self.delay_var]

        for i, (lbl, var) in enumerate(zip(labels, vars_), start=1):
            ctk.CTkLabel(settings_frame, text=lbl, font=ctk.CTkFont(size=12)).grid(row=i, column=0, padx=(15, 5), pady=5, sticky="w")
            ctk.CTkEntry(settings_frame, textvariable=var, width=80, height=30, justify="center").grid(row=i, column=1, padx=(5, 15), pady=5)

        settings_frame.grid_columnconfigure(0, weight=1)

        # OCR Debug Checkbox
        self.debug_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(root, text="OCR Debug Modu", variable=self.debug_var, font=ctk.CTkFont(size=12)).pack(pady=(0, 8))

        # Butonlar (yan yana)
        btn_frame = ctk.CTkFrame(root, fg_color="transparent")
        btn_frame.pack(pady=5)

        self.start_btn = ctk.CTkButton(
            btn_frame, text="Başlat  (F8)", width=160, height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2ecc71", hover_color="#27ae60", text_color="black",
            command=self.start_bot
        )
        self.start_btn.grid(row=0, column=0, padx=8)

        self.stop_btn = ctk.CTkButton(
            btn_frame, text="Durdur  (F9)", width=160, height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#e74c3c", hover_color="#c0392b", text_color="white",
            state="disabled", command=self.stop_bot
        )
        self.stop_btn.grid(row=0, column=1, padx=8)

        # Durum Label
        status_frame = ctk.CTkFrame(root)
        status_frame.pack(fill="x", padx=15, pady=12)
        self.log_lbl = ctk.CTkLabel(status_frame, text="Durum: Bekliyor", font=ctk.CTkFont(size=13, weight="bold"), text_color="#5dade2")
        self.log_lbl.pack(pady=10)

        keyboard.on_release_key('f8', lambda e: self.start_bot())
        keyboard.on_release_key('f9', lambda e: self.stop_bot())

        self.load_settings()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Güncelleme kontrolünü arka planda başlat
        threading.Thread(target=check_for_updates, args=(self._on_update_found,), daemon=True).start()

    def _on_update_found(self, latest_version, download_url):
        self.root.after(0, lambda: self._show_update_dialog(latest_version, download_url))

    def _show_update_dialog(self, latest_version, download_url):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Güncelleme Mevcut")
        dialog.geometry("380x210")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Yeni Güncelleme Mevcut!", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(dialog, text=f"v{VERSION}  →  v{latest_version}", font=ctk.CTkFont(size=13), text_color="#2ecc71").pack(pady=(0, 8))

        self._update_status_lbl = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=11))
        self._update_status_lbl.pack(pady=(0, 8))

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack()

        update_btn = ctk.CTkButton(
            btn_row, text="İndir ve Hazırla", width=150, height=36,
            fg_color="#2ecc71", hover_color="#27ae60", text_color="black",
            font=ctk.CTkFont(weight="bold")
        )

        def on_update_click():
            update_btn.configure(state="disabled")
            self._update_status_lbl.configure(text="İndiriliyor...", text_color="#e67e22")
            def do():
                def done():
                    self._update_status_lbl.configure(
                        text="Hazır! Uygulamayı kapatıp tekrar açın.", text_color="#2ecc71"
                    )
                apply_update(download_url, on_progress=lambda: self.root.after(0, done))
            threading.Thread(target=do, daemon=True).start()

        update_btn.configure(command=on_update_click)
        update_btn.grid(row=0, column=0, padx=8)

        ctk.CTkButton(
            btn_row, text="Sonra", width=150, height=36,
            fg_color="#555", hover_color="#444",
            command=dialog.destroy
        ).grid(row=0, column=1, padx=8)

    def load_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            return
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                s = json.load(f)
            self.tess_path_var.set(s.get("tess_path", self.tess_path_var.get()))
            self.moais_var.set(s.get("moais", self.moais_var.get()))
            self.shady_var.set(s.get("shady", self.shady_var.get()))
            self.micro_var.set(s.get("micro", self.micro_var.get()))
            self.delay_var.set(s.get("esc_delay", self.delay_var.get()))
        except Exception:
            pass

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "tess_path": self.tess_path_var.get(),
                    "moais": self.moais_var.get(),
                    "shady": self.shady_var.get(),
                    "micro": self.micro_var.get(),
                    "esc_delay": self.delay_var.get(),
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def on_close(self):
        self.save_settings()
        self.root.destroy()

    def update_log(self, text, color="#ffffff"):
        self.log_lbl.configure(text=text, text_color=color)
        self.root.update()

    def _install_tesseract(self, dialog, status_lbl, install_btn):
        import ctypes
        install_btn.configure(state="disabled")
        status_lbl.configure(text="Yönetici izni isteniyor...", text_color="#e67e22")
        self.root.update()
        try:
            # Yönetici yetkisiyle winget'i çalıştır, kullanıcı kurulumu görebilsin
            bat = (
                "@echo off\n"
                "echo Tesseract-OCR kuruluyor, lutfen bekleyin...\n"
                "winget install -e --id UB-Mannheim.TesseractOCR "
                "--accept-package-agreements --accept-source-agreements\n"
                "echo.\n"
                "echo Kurulum tamamlandi, bu pencereyi kapatabilirsiniz.\n"
                "pause\n"
            )
            bat_path = tempfile.mktemp(suffix=".bat")
            with open(bat_path, "w") as f:
                f.write(bat)

            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", "cmd.exe", f"/c \"{bat_path}\"", None, 1
            )

            status_lbl.configure(text="Kurulum penceresi açıldı. Tamamlanınca botu başlatın.", text_color="#2ecc71")

            # Tesseract kurulana kadar arka planda kontrol et
            threading.Thread(target=self._wait_for_tesseract, args=(status_lbl,), daemon=True).start()
        except Exception as e:
            status_lbl.configure(text=f"Hata: {e}", text_color="#e74c3c")
            install_btn.configure(state="normal")

    def _wait_for_tesseract(self, status_lbl):
        tess_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        for _ in range(120):  # 10 dakika boyunca 5'er saniyede kontrol et
            time.sleep(5)
            if os.path.exists(tess_path):
                self.tess_path_var.set(tess_path)
                self.root.after(0, lambda: status_lbl.configure(
                    text="Tesseract kuruldu! Artık botu başlatabilirsiniz.", text_color="#2ecc71"
                ))
                return

    def _show_tesseract_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Tesseract Kurulumu Gerekli")
        dialog.geometry("380x220")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Tesseract-OCR Bulunamadı", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(dialog, text="Bot ekranı okuyabilmek için Tesseract-OCR'a\nihtiyaç duyar. Otomatik kurulsun mu?",
                     font=ctk.CTkFont(size=12), justify="center").pack(pady=(0, 15))

        status_lbl = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=11))
        status_lbl.pack(pady=(0, 8))

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack()

        install_btn = ctk.CTkButton(
            btn_row, text="Evet, Kur", width=150, height=36,
            fg_color="#2ecc71", hover_color="#27ae60", text_color="black",
            font=ctk.CTkFont(weight="bold")
        )
        install_btn.configure(command=lambda: threading.Thread(
            target=self._install_tesseract, args=(dialog, status_lbl, install_btn), daemon=True
        ).start())
        install_btn.grid(row=0, column=0, padx=8)

        ctk.CTkButton(
            btn_row, text="İptal", width=150, height=36,
            fg_color="#555", hover_color="#444",
            command=dialog.destroy
        ).grid(row=0, column=1, padx=8)

    def start_bot(self):
        if not self.running:
            tess_path = self.tess_path_var.get()
            if not os.path.exists(tess_path):
                self._show_tesseract_dialog()
                return

            pytesseract.pytesseract.tesseract_cmd = tess_path
            self.running = True

            self.root.after(0, lambda: self.start_btn.configure(state="disabled"))
            self.root.after(0, lambda: self.stop_btn.configure(state="normal"))
            self.update_log("Durum: Çalışıyor...", "#2ecc71")

            threading.Thread(target=self.bot_loop, daemon=True).start()

    def stop_bot(self):
        if self.running:
            self.running = False
            elapsed = time.time() - self.start_time
            self.root.after(0, lambda: self.start_btn.configure(state="normal"))
            self.root.after(0, lambda: self.stop_btn.configure(state="disabled"))
            self.update_log(f"Durduruldu | {self.reroll_count} deneme, {elapsed:.1f}sn", "#e74c3c")

    def _show_debug_window(self, text, thresh_img):
        pil_img = Image.fromarray(thresh_img)
        max_w = 600
        if pil_img.width > max_w:
            ratio = max_w / pil_img.width
            pil_img = pil_img.resize((max_w, int(pil_img.height * ratio)), Image.NEAREST)

        if self.debug_win is None or not self.debug_win.winfo_exists():
            self.debug_win = tk.Toplevel(self.root)
            self.debug_win.title("OCR Debug")
            self.debug_win.attributes("-topmost", True)
            self.debug_win.configure(bg="#2b2b2b")
            self.debug_win.protocol("WM_DELETE_WINDOW", lambda: setattr(self, 'debug_win', None) or self.debug_win.destroy())

            self._debug_text = scrolledtext.ScrolledText(self.debug_win, width=70, height=10, font=("Courier", 9), bg="#1d1d1d", fg="#e0e0e0", insertbackground="white")
            self._debug_text.pack(padx=5, pady=(5, 2))

            self.debug_img_label = tk.Label(self.debug_win, bg="#2b2b2b")
            self.debug_img_label.pack(padx=5, pady=(2, 5))

        self._debug_text.config(state=tk.NORMAL)
        self._debug_text.delete("1.0", tk.END)
        self._debug_text.insert(tk.END, text)
        self._debug_text.config(state=tk.DISABLED)

        photo = ImageTk.PhotoImage(pil_img)
        self.debug_img_label.config(image=photo)
        self.debug_img_label.image = photo

    def get_screen_data(self):
        screen_width, screen_height = pyautogui.size()

        x = int(screen_width * 0.70)
        y = int(screen_height * 0.60)
        w = int(screen_width * 0.30)
        h = int(screen_height * 0.40)

        screenshot = pyautogui.screenshot(region=(x, y, w, h))
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        img = cv2.resize(img, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(thresh, config=custom_config)

        if self.debug_var.get():
            self.root.after(0, lambda t=text, img=thresh.copy(): self._show_debug_window(t, img))

        return text

    def bot_loop(self):
        target_moais = self.moais_var.get()
        target_shady = self.shady_var.get()
        target_micro = self.micro_var.get()
        esc_delay = self.delay_var.get()

        self.reroll_count = 0
        self.start_time = time.time()

        while self.running:
            try:
                text = self.get_screen_data()

                moais_count = -1
                shady_count = -1
                micro_count = -1

                lines = text.split('\n')
                for line in lines:
                    if 'moais' in line.lower():
                        nums = re.findall(r'\d+', line)
                        if nums: moais_count = int(nums[-1])
                    elif 'shady' in line.lower() and 'guy' in line.lower():
                        nums = re.findall(r'\d+', line)
                        if nums: shady_count = int(nums[-1])
                    elif 'microwave' in line.lower():
                        nums = re.findall(r'\d+', line)
                        if nums: micro_count = int(nums[-1])

                if moais_count == -1 and shady_count == -1 and micro_count == -1:
                    time.sleep(0.5)
                    continue

                elapsed = time.time() - self.start_time
                self.update_log(
                    f"Moais: {max(0,moais_count)} | Shady: {max(0,shady_count)} | Micro: {max(0,micro_count)}  [{self.reroll_count} deneme, {elapsed:.0f}sn]",
                    "#e67e22"
                )

                if moais_count >= target_moais and shady_count >= target_shady and micro_count >= target_micro:
                    elapsed = time.time() - self.start_time
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    self.update_log(f"HEDEF BULUNDU!  {self.reroll_count} denemede {elapsed:.1f}sn", "#2ecc71")

                    time.sleep(esc_delay)
                    keyboard.press('esc')
                    time.sleep(0.1)
                    keyboard.release('esc')

                    self.running = False
                    self.root.after(0, lambda: self.start_btn.configure(state="normal"))
                    self.root.after(0, lambda: self.stop_btn.configure(state="disabled"))
                    break
                else:
                    self.reroll_count += 1
                    keyboard.press('r')
                    time.sleep(1.2)
                    keyboard.release('r')
                    time.sleep(0.2)

            except Exception as e:
                self.update_log("HATA: Konsolu inceleyin", "#e74c3c")
                print("Bot hatası:", e)
                self.stop_bot()
                break


if __name__ == "__main__":
    try:
        import pytesseract
        import cv2
        import numpy
        import pyautogui
        import keyboard
        import customtkinter
        from PIL import Image, ImageTk
    except ImportError:
        import tkinter.messagebox as mb
        mb.showerror("Eksik Modül", "Gerekli kütüphaneler eksik.\nLütfen 'pip install pyautogui pytesseract opencv-python keyboard numpy pillow customtkinter' komutu ile modülleri kurun.")
        exit(1)

    root = ctk.CTk()
    app = MegabonkBot(root)
    root.mainloop()

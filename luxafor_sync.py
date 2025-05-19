
import os
import sys
import time
import threading
import requests
import configparser
import platform
import ctypes
import subprocess
import webbrowser
import customtkinter as ctk
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

CONFIG_FILE = "settings.cfg"
LOG_FILE = "luxafor_error.log"
access_token = None
last_refresh = 0
current_status = ["Unbekannt"]
previous_status = [None]
tray_icon = None
main_window = None

COLOR_MAP = {
    "available": "green",
    "away": "yellow",
    "busy": "red"
}

def log_error(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def set_color(user_id, color):
    try:
        requests.post("https://api.luxafor.com/webhook/v1/actions/solid_color", json={
            "userId": user_id,
            "actionFields": {"color": color}
        }, headers={"Content-Type": "application/json"})
    except Exception as e:
        log_error(f"Luxafor Set Color Error: {e}")

def set_luxafor(user_id, status):
    color = COLOR_MAP.get(status, "blue")
    set_color(user_id, color)
    previous_status[0] = status

def get_config():
    c = configparser.ConfigParser()
    c.read(CONFIG_FILE)
    return {
        "client_id": c["ZOHO"]["client_id"],
        "client_secret": c["ZOHO"]["client_secret"],
        "refresh_token": c["ZOHO"]["refresh_token"],
        "luxafor_user_id": c["LUXAFOR"]["user_id"],
        "start_in_tray": c["APP"].get("start_in_tray", "false").lower() == "true"
    }

def check_or_setup_config():
    if not os.path.exists(CONFIG_FILE):
        return False
    try:
        c = configparser.ConfigParser()
        c.read(CONFIG_FILE)
        c["ZOHO"]["client_id"]
        c["ZOHO"]["client_secret"]
        c["ZOHO"]["refresh_token"]
        c["LUXAFOR"]["user_id"]
        return True
    except:
        return False

def refresh_token(config):
    global access_token, last_refresh
    if time.time() - last_refresh < 1800 and access_token:
        return
    try:
        r = requests.post("https://accounts.zoho.eu/oauth/v2/token", data={
            "refresh_token": config["refresh_token"],
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "grant_type": "refresh_token"
        })
        r.raise_for_status()
        access_token = r.json()["access_token"]
        last_refresh = time.time()
    except Exception as e:
        log_error(f"Token-Refresh: {e}")

def get_status():
    if not access_token:
        return None
    try:
        r = requests.get("https://cliq.zoho.eu/api/v2/statuses/current",
                         headers={"Authorization": f"Zoho-oauthtoken {access_token}"})
        r.raise_for_status()
        data = r.json().get("data", {})
        return data.get("transient_status", {}).get("code") or data.get("code")
    except Exception as e:
        log_error(f"Status-Fehler: {e}")
        return None

def sync_loop(config, label=None):
    while True:
        refresh_token(config)
        status = get_status()
        if status:
            set_luxafor(config["luxafor_user_id"], status)
            current_status[0] = status
            if label:
                label.configure(text=f"Status: {status}")
        time.sleep(4)

def run_main_gui():
    global main_window
    config = get_config()
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    win = ctk.CTk()
    win.title("Luxafor Status – Made by einfachnikita")
    win.geometry("300x140")
    win.resizable(False, False)

    label = ctk.CTkLabel(win, text="Status: Lade...", font=("Segoe UI", 18))
    label.pack(pady=30)

    threading.Thread(target=sync_loop, args=(config, label), daemon=True).start()
    main_window = win
    win.mainloop()

def open_token_generator():
    win = ctk.CTkToplevel()
    win.title("Zoho Token Generator – Made by einfachnikita")
    win.geometry("600x600")
    win.resizable(False, False)

    vars = {
        "client_id": ctk.StringVar(),
        "client_secret": ctk.StringVar(),
        "redirect_uri": ctk.StringVar(value="http://localhost"),
        "scope": ctk.StringVar(value="ZohoCliq.Users.READ"),
        "code": ctk.StringVar(),
        "access_token": ctk.StringVar(),
        "refresh_token": ctk.StringVar()
    }

    def open_auth():
        url = (
            f"https://accounts.zoho.eu/oauth/v2/auth?"
            f"scope={vars['scope'].get().strip()}&"
            f"client_id={vars['client_id'].get().strip()}&"
            f"response_type=code&access_type=offline&"
            f"redirect_uri={vars['redirect_uri'].get().strip()}"
        )
        webbrowser.open(url)

    def get_tokens():
        data = {
            "grant_type": "authorization_code",
            "client_id": vars["client_id"].get().strip(),
            "client_secret": vars["client_secret"].get().strip(),
            "redirect_uri": vars["redirect_uri"].get().strip(),
            "code": vars["code"].get().strip()
        }
        try:
            r = requests.post("https://accounts.zoho.eu/oauth/v2/token", data=data)
            r.raise_for_status()
            tokens = r.json()
            vars["access_token"].set(tokens.get("access_token", ""))
            vars["refresh_token"].set(tokens.get("refresh_token", ""))
            with open("refresh_token.txt", "w", encoding="utf-8") as f:
                f.write(tokens.get("refresh_token", ""))
        except Exception as e:
            vars["access_token"].set("Fehler")
            vars["refresh_token"].set("Fehler")
            log_error(f"Token Abruf Fehler: {e}")

    for label, key in [("Client ID", "client_id"), ("Client Secret", "client_secret"),
                       ("Redirect URI", "redirect_uri"), ("Scope", "scope"), ("Code", "code")]:
        ctk.CTkLabel(win, text=label).pack()
        ctk.CTkEntry(win, textvariable=vars[key]).pack()

    ctk.CTkButton(win, text="🔐 Auth-Link öffnen", command=open_auth).pack(pady=5)
    ctk.CTkButton(win, text="✅ Token abrufen", command=get_tokens).pack(pady=10)

    ctk.CTkLabel(win, text="Access Token").pack()
    ctk.CTkEntry(win, textvariable=vars["access_token"]).pack()
    ctk.CTkLabel(win, text="Refresh Token").pack()
    ctk.CTkEntry(win, textvariable=vars["refresh_token"]).pack()

def run_setup_gui():
    app = ctk.CTk()
    app.title("Luxafor Setup – Made by einfachnikita")
    app.geometry("500x430")
    app.resizable(False, False)

    vars = {
        "client_id": ctk.StringVar(),
        "client_secret": ctk.StringVar(),
        "refresh_token": ctk.StringVar(),
        "user_id": ctk.StringVar(),
        "tray": ctk.BooleanVar(value=False)
    }

    ctk.CTkButton(app, text="🔐 Token Generator", command=open_token_generator, width=160).place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)

    for label, var in list(vars.items())[:-1]:
        ctk.CTkLabel(app, text=label.replace("_", " ").title()).pack(pady=(10, 0))
        ctk.CTkEntry(app, textvariable=var, show="*" if "secret" in label or "token" in label else None).pack()

    ctk.CTkCheckBox(app, text="Beim nächsten Start im Tray starten", variable=vars["tray"]).pack(pady=10)

    def save_and_start():
        config = configparser.ConfigParser()
        config["ZOHO"] = {
            "client_id": vars["client_id"].get().strip(),
            "client_secret": vars["client_secret"].get().strip(),
            "refresh_token": vars["refresh_token"].get().strip()
        }
        config["LUXAFOR"] = {
            "user_id": vars["user_id"].get().strip()
        }
        config["APP"] = {
            "start_in_tray": str(vars["tray"].get()).lower()
        }
        with open(CONFIG_FILE, "w") as f:
            config.write(f)
        app.destroy()
        run_main_gui()

    ctk.CTkButton(app, text="💾 Speichern & Starten", command=save_and_start).pack(pady=20)
    app.mainloop()

def create_tray_icon():
    image = Image.new("RGB", (64, 64), "black")
    d = ImageDraw.Draw(image)
    d.ellipse((16, 16, 48, 48), fill="blue")
    return image

def on_open(icon, item):
    threading.Thread(target=run_main_gui, daemon=True).start()

def on_config(icon, item):
    subprocess.Popen(["notepad.exe", CONFIG_FILE], shell=True)

def on_exit(icon, item):
    icon.stop()
    sys.exit()

def start_tray():
    config = get_config()
    threading.Thread(target=sync_loop, args=(config,), daemon=True).start()

    menu = Menu(
        MenuItem("Öffnen", on_open),
        MenuItem("Config", on_config),
        MenuItem("Exit", on_exit)
    )
    icon = Icon("LuxaforSync", create_tray_icon(), menu=menu)
    icon.run()

if __name__ == "__main__":
    if platform.system() == "Windows":
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    if not check_or_setup_config():
        run_setup_gui()
    else:
        cfg = get_config()
        if cfg["start_in_tray"]:
            start_tray()
        else:
            run_main_gui()

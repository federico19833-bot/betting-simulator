import sys
import os
import subprocess
import webbrowser
import threading
import time
import pystray
from PIL import Image, ImageDraw

BOT_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_URL = "https://web-weld-gamma-28.vercel.app"
bot_process = None

def create_icon():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill="#22c55e")
    draw.ellipse([16, 16, 48, 48], fill="#0f172a")
    draw.text((22, 18), "B", fill="#22c55e", font=None)
    return img

def start_bot():
    global bot_process
    if bot_process and bot_process.poll() is None:
        return
    bot_process = subprocess.Popen(
        [sys.executable, "-u", os.path.join(BOT_DIR, "main.py")],
        cwd=BOT_DIR,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

def stop_bot():
    global bot_process
    if bot_process and bot_process.poll() is None:
        bot_process.terminate()
        bot_process = None

def open_dashboard(icon, item):
    webbrowser.open(DASHBOARD_URL)

def bot_status(icon, item):
    global bot_process
    if bot_process and bot_process.poll() is None:
        icon.notify("Bot ATTIVO - Scan ogni 60s", "Betting Simulator")
    else:
        icon.notify("Bot FERMO", "Betting Simulator")

def action_start(icon, item):
    start_bot()
    icon.notify("Bot avviato!", "Betting Simulator")

def action_stop(icon, item):
    stop_bot()
    icon.notify("Bot fermato!", "Betting Simulator")

def action_exit(icon, item):
    stop_bot()
    icon.stop()
    os._exit(0)

def main():
    start_bot()
    icon = pystray.Icon(
        "betting_simulator",
        create_icon(),
        "Betting Simulator",
        menu=pystray.Menu(
            pystray.MenuItem("Dashboard", open_dashboard),
            pystray.MenuItem("Stato Bot", bot_status),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Avvia Bot", action_start),
            pystray.MenuItem("Ferma Bot", action_stop),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Esci", action_exit),
        ),
    )
    icon.run()

if __name__ == "__main__":
    main()

import asyncio
import threading
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler
from telegram.error import TelegramError
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, INITIAL_BALANCE, STAKE
from database import get_statistiche_giornaliere, get_tutte_giocate
from analysis import generate_equity_chart
import pandas as pd

bot = None
app = None

async def start_command(update: Update, context):
    await update.message.reply_text("Bot attivo! Usa /status per le statistiche.")

async def status_command(update: Update, context):
    giocate = get_tutte_giocate()
    df = pd.DataFrame(giocate) if giocate else pd.DataFrame()
    if len(df) == 0:
        await update.message.reply_text("Nessuna giocata nel database.")
        return
    wins = len(df[df["esito"] == "VINTA"])
    losses = len(df[df["esito"] == "PERSA"])
    in_corso = len(df[df["esito"] == "IN_CORSO"])
    total = len(df)
    winrate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    df["profitto_netto"] = df["profitto_netto"].astype(float)
    profit = df["profitto_netto"].sum()
    msg = (
        f"STATUS BOT - Attivo\n"
        f"Giocate: {total}\n"
        f"Vinte: {wins}\n"
        f"Perse: {losses}\n"
        f"In corso: {in_corso}\n"
        f"Win Rate: {winrate:.1f}%\n"
        f"Profitto: {profit:+.2f}Euro"
    )
    await update.message.reply_text(msg)

def start_polling():
    global app
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        return
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.run_polling(allowed_updates=["message"])

def init_bot():
    global bot
    if TELEGRAM_TOKEN and TELEGRAM_TOKEN != "YOUR_TELEGRAM_BOT_TOKEN":
        bot = Bot(token=TELEGRAM_TOKEN)
        try:
            bot.set_my_commands([
                ("start", "Verifica se il bot e attivo"),
                ("status", "Statistiche complete"),
            ])
        except:
            pass
        t = threading.Thread(target=start_polling, daemon=True)
        t.start()
        return True
    return False

async def invia_notifica_entrata(giocata_id, match, campionato, quota, volume):
    if not bot:
        return
    msg = (
        f"🟢 NUOVA GIOCATA ENTRATA\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"ID: #{giocata_id}\n"
        f"Match: {match}\n"
        f"Campionato: {campionato}\n"
        f"Quota: {quota}\n"
        f"Volume: {volume:.0f}€\n"
        f"Stake: {STAKE}€"
    )
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    except TelegramError as e:
        print(f"[TELEGRAM] Errore notifica: {e}")

async def invia_report_giornaliero():
    if not bot:
        print("[TELEGRAM] Bot non configurato, salto report.")
        return
    giocate = get_statistiche_giornaliere()
    if not giocate:
        msg = "📭 Nessuna giocata registrata oggi."
        try:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        except TelegramError as e:
            print(f"[TELEGRAM] Errore report: {e}")
        return
    df = pd.DataFrame(giocate)
    wins = len(df[df["esito"] == "VINTA"])
    losses = len(df[df["esito"] == "PERSA"])
    in_corso = len(df[df["esito"] == "IN_CORSO"])
    total = len(df)
    winrate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    df["profitto_netto"] = df["profitto_netto"].astype(float)
    profit = df["profitto_netto"].sum()
    msg = (
        f"📊 REPORT GIORNALIERO\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📅 {pd.Timestamp.now().strftime('%d/%m/%Y')}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Giocate totali: {total}\n"
        f"✅ Vinte: {wins}\n"
        f"❌ Perse: {losses}\n"
        f"⏳ In corso: {in_corso}\n"
        f"📈 Win Rate: {winrate:.1f}%\n"
        f"💰 Profitto netto: {profit:+.2f}€\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    except TelegramError as e:
        print(f"[TELEGRAM] Errore report testo: {e}")
    chart_path = generate_equity_chart()
    if chart_path:
        try:
            with open(chart_path, "rb") as f:
                await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=f)
        except TelegramError as e:
            print(f"[TELEGRAM] Errore invio grafico: {e}")

async def invia_heartbeat():
    if not bot:
        return
    msg = f"Bot AVVIATO - {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}"
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    except TelegramError as e:
        print(f"[TELEGRAM] Errore heartbeat: {e}")

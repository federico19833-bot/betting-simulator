import asyncio
import threading
import json
import os
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.error import TelegramError
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, INITIAL_BALANCE, STAKE, MIN_ODDS, MAX_ODDS, VOLUME_THRESHOLD
from database import get_statistiche_giornaliere, get_tutte_giocate
from analysis import generate_equity_chart
import pandas as pd

bot = None
app = None

async def start_command(update: Update, context):
    msg = (
        "🤖 *Betting Bot - Over 0.5*\n"
        "━━━━━━━━━━━━━━━━\n"
        "Puoi scrivermi in italiano, capisco:\n\n"
        "• `status` — statistiche generali\n"
        "• `mercati` — eventi live trovati\n"
        "• `monitorati` — partite in osservazione\n"
        "• `scan` — forza una scansione ora\n"
        "• `storico` — ultime giocate\n"
        "• `config` — configurazione attuale\n"
        "• `help` — questo messaggio"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def status_command(update: Update, context):
    giocate = get_tutte_giocate()
    df = pd.DataFrame(giocate) if giocate else pd.DataFrame()
    if len(df) == 0:
        await update.message.reply_text("📭 Nessuna giocata nel database.")
        return
    wins = len(df[df["esito"] == "VINTA"])
    losses = len(df[df["esito"] == "PERSA"])
    in_corso = len(df[df["esito"] == "IN_CORSO"])
    total = len(df)
    winrate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    df["profitto_netto"] = df["profitto_netto"].astype(float)
    profit = df["profitto_netto"].sum()
    msg = (
        f"📊 *STATUS BOT*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🔄 Scan ogni 30s (Smarkets + Betfair)\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"Giocate: {total}\n"
        f"✅ Vinte: {wins}\n"
        f"❌ Perse: {losses}\n"
        f"⏳ In corso: {in_corso}\n"
        f"📈 Win Rate: {winrate:.1f}%\n"
        f"💰 Profitto: {profit:+.2f}€\n"
        f"🏦 Capitale: {INITIAL_BALANCE + profit:.2f}€\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"Range: {MIN_ODDS}-{MAX_ODDS} | Soglia: {VOLUME_THRESHOLD}€"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def markets_command(update: Update, context):
    scan_file = os.path.join(os.path.dirname(__file__), "last_scan.json")
    if not os.path.exists(scan_file):
        await update.message.reply_text("Nessun dato scan disponibile.")
        return
    with open(scan_file, "r", encoding="utf-8") as f:
        events = json.load(f)
    if not events:
        await update.message.reply_text("Nessun mercato Over 0.5 attivo in questo momento.")
        return
    lines = [f"📡 *Mercati Live* ({len(events)})"]
    lines.append("━━━━━━━━━━━━━━━━")
    for e in events:
        src = e.get("source", "?")
        match = e.get("match", "?")
        quota = e.get("quota", 0)
        vol = e.get("volume", 0)
        in_range = "✅" if MIN_ODDS <= quota <= MAX_ODDS else ""
        lines.append(f"{in_range} {match}")
        lines.append(f"   Quota: {quota} | Vol: {vol}€ | {src}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def tracked_command(update: Update, context):
    track_file = os.path.join(os.path.dirname(__file__), "tracked_matches.json")
    if not os.path.exists(track_file):
        await update.message.reply_text("Nessun match monitorato.")
        return
    with open(track_file, "r", encoding="utf-8") as f:
        tracked = json.load(f)
    if not tracked:
        await update.message.reply_text("Nessun match in monitoraggio.")
        return
    lines = [f"🔍 *Monitoraggio Balene* ({len(tracked)})"]
    lines.append("━━━━━━━━━━━━━━━━")
    for eid, t in tracked.items():
        match = t.get("match", "?")
        price = t.get("last_price", 0)
        vol = t.get("volume", 0)
        whale = t.get("whale_max", 0)
        entered = "✅ ENTRATA" if t.get("entered") else "⏳ IN ATTESA"
        whale_str = f"🐋 {whale}€" if whale > 0 else ""
        lines.append(f"{match}")
        lines.append(f"   Quota: {price} | Vol: {vol}€ {whale_str}")
        lines.append(f"   Stato: {entered}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def history_command(update: Update, context):
    giocate = get_tutte_giocate()
    if not giocate:
        await update.message.reply_text("Nessuna giocata in archivio.")
        return
    lines = [f"📜 *Storico Giocate* ({len(giocate)})"]
    lines.append("━━━━━━━━━━━━━━━━")
    for g in giocate[:10]:
        icon = "✅" if g["esito"] == "VINTA" else "❌" if g["esito"] == "PERSA" else "⏳"
        profit = g["profitto_netto"]
        profit_str = f"+{profit:.2f}€" if profit >= 0 else f"{profit:.2f}€"
        date = g["orario"][:10]
        lines.append(f"{icon} #{g['id']} {date} - {g['match']}")
        lines.append(f"   Quota: {g['quota_reale']} | {profit_str}")
    if len(giocate) > 10:
        lines.append(f"... e altre {len(giocate)-10} giocate (vedi sito per completo)")
    lines.append("━━━━━━━━━━━━━━━━")
    lines.append(f"📊 Sito: https://federico19833-bot.github.io/betting-simulator/")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def config_command(update: Update, context):
    msg = (
        f"⚙️ *Configurazione*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"Range quota: {MIN_ODDS} - {MAX_ODDS}\n"
        f"Soglia volume: {VOLUME_THRESHOLD}€\n"
        f"Stake: {STAKE}€\n"
        f"Scan: ogni 30s\n"
        f"Fonti: Smarkets + Betfair\n"
        f"Risoluzione: 180 min dopo fischio\n"
        f"Verifica: TheSportsDB + Smarkets"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def scan_command(update: Update, context):
    await update.message.reply_text("🔄 Forzo scansione...")
    try:
        from data_source import scan_markets
        results = scan_markets()
        if results:
            await update.message.reply_text(f"✅ Scansione completata! {len(results)} segnali trovati.")
        else:
            await update.message.reply_text("✅ Scansione completata. Nessun segnale al momento.")
    except Exception as e:
        await update.message.reply_text(f"❌ Errore scansione: {e}")

async def help_command(update: Update, context):
    await start_command(update, context)

async def handle_message(update: Update, context):
    text = update.message.text.lower().strip()
    
    if text in ["status", "statistiche", "stats"]:
        await status_command(update, context)
    elif text in ["mercati", "mercato", "markets", "live"]:
        await markets_command(update, context)
    elif text in ["monitorati", "monitoraggio", "tracked", "balene"]:
        await tracked_command(update, context)
    elif text in ["storico", "history", "giocate"]:
        await history_command(update, context)
    elif text in ["config", "configurazione", "settings"]:
        await config_command(update, context)
    elif text in ["scan", "scansiona", "refresh"]:
        await scan_command(update, context)
    elif text in ["help", "aiuto", "comandi", "start"]:
        await help_command(update, context)
    else:
        await update.message.reply_text(
            f"Non ho capito. Scrivi `help` per i comandi disponibili.",
            parse_mode="Markdown"
        )

def start_polling():
    global app
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        return
    try:
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("status", status_command))
        app.add_handler(CommandHandler("markets", markets_command))
        app.add_handler(CommandHandler("tracked", tracked_command))
        app.add_handler(CommandHandler("history", history_command))
        app.add_handler(CommandHandler("config", config_command))
        app.add_handler(CommandHandler("scan", scan_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.run_polling(allowed_updates=["message"])
    except Exception as e:
        print(f"[TELEGRAM] ERRORE polling: {e}")

def init_bot():
    global bot
    if TELEGRAM_TOKEN and TELEGRAM_TOKEN != "YOUR_TELEGRAM_BOT_TOKEN":
        bot = Bot(token=TELEGRAM_TOKEN)
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(bot.set_my_commands([
                ("start", "Menu interattivo"),
                ("status", "Statistiche complete"),
                ("markets", "Mercati live trovati"),
                ("tracked", "Match monitorati"),
                ("history", "Storico giocate"),
                ("config", "Configurazione attuale"),
                ("scan", "Forza scansione ora"),
            ]))
            loop.close()
        except:
            pass
        t = threading.Thread(target=start_polling, daemon=True)
        t.start()
        return True
    return False

async def invia_notifica_esito(giocata_id, match, campionato, quota, esito, profitto):
    if not bot:
        return
    icon = "✅" if esito == "VINTA" else "❌"
    msg = (
        f"{icon} GIOCATA RISOLTA\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"ID: #{giocata_id}\n"
        f"Match: {match}\n"
        f"Campionato: {campionato}\n"
        f"Quota: {quota}\n"
        f"Esito: {esito}\n"
        f"Profitto: {profitto:+.2f}€"
    )
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    except TelegramError as e:
        print(f"[TELEGRAM] Errore notifica esito: {e}")

async def invia_notifica_errore(giocata_id, match, smarkets, sportsdb):
    if not bot:
        return
    msg = (
        f"⚠️ DISCREPANZA RISULTATI\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"ID: #{giocata_id}\n"
        f"Match: {match}\n"
        f"Smarkets: {'GOAL' if smarkets else '0-0'}\n"
        f"TheSportsDB: {'GOAL' if sportsdb else '0-0'}\n"
        f"⏳ In attesa di riconciliazione..."
    )
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    except TelegramError as e:
        print(f"[TELEGRAM] Errore notifica discrepanza: {e}")

async def invia_notifica_entrata(giocata_id, match, campionato, quota, volume, open_date=""):
    if not bot:
        return
    kick_off = ""
    if open_date:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(open_date.replace("Z", "+00:00"))
            kick_off = f"\nKick-off: {dt.strftime('%d/%m %H:%M')}"
        except:
            kick_off = f"\nKick-off: {open_date[:16]}"
    msg = (
        f"🟢 NUOVA GIOCATA ENTRATA\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"ID: #{giocata_id}\n"
        f"Match: {match}\n"
        f"Campionato: {campionato}{kick_off}\n"
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

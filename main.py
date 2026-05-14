import asyncio
import time
import schedule
from datetime import datetime
from config import POLL_INTERVAL_SECONDS
from database import init_db
from data_source import scan_markets
from trading import execute_entry, check_and_resolve_pending
from telegram_bot import init_bot, invia_notifica_entrata, invia_report_giornaliero, invia_heartbeat
from analysis import generate_equity_chart

bot_ready = False

async def poll_markets():
    global bot_ready
    print(f"\n[MAIN] Scan {datetime.now().strftime('%H:%M:%S')}")
    matches = scan_markets()
    for m in matches:
        giocata_id = execute_entry(m["match"], m["campionato"], m["volume"], m["quota"], m.get("event_id", ""))
        if bot_ready:
            await invia_notifica_entrata(giocata_id, m["match"], m["campionato"], m["quota"], m["volume"])
    check_and_resolve_pending()

async def daily_report():
    print(f"[MAIN] Report giornaliero {datetime.now().strftime('%d/%m/%Y')}")
    await invia_report_giornaliero()

async def heartbeat():
    global bot_ready
    if bot_ready:
        await invia_heartbeat()

def run_scheduled():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(poll_markets())
    except Exception as e:
        print(f"[MAIN] Errore nel ciclo: {e}")
    finally:
        loop.close()

def run_daily():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(daily_report())
    except Exception as e:
        print(f"[MAIN] Errore report giornaliero: {e}")
    finally:
        loop.close()

def main():
    global bot_ready
    print("=" * 50)
    print("  BETTING SIMULATOR - Strategia 1.05")
    print("=" * 50)
    init_db()
    print("[MAIN] Database inizializzato")
    bot_ready = init_bot()
    if bot_ready:
        print("[MAIN] Bot Telegram configurato")
    else:
        print("[MAIN] Telegram NON configurato (metti TOKEN e CHAT_ID in config.py)")
    schedule.every(POLL_INTERVAL_SECONDS).seconds.do(run_scheduled)
    schedule.every().day.at("23:00").do(run_daily)
    schedule.every().day.at("18:00").do(lambda: asyncio.run(heartbeat()))
    print(f"[MAIN] Scan ogni {POLL_INTERVAL_SECONDS}s | Report ore 23:00 | Heartbeat 18:00")
    print("[MAIN] In esecuzione... (CTRL+C per fermare)\n")
    if bot_ready:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(heartbeat())
        loop.close()
    run_scheduled()
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[MAIN] Arresto...")
        generate_equity_chart()
        print("[MAIN] Grafico finale salvato. Arrivederci!")

if __name__ == "__main__":
    main()

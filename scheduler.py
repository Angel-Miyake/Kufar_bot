import asyncio
import threading

from config import CHECK_INTERVAL

from logger import log
from db import (
    get_all_filters,
    ad_already_sent,
    save_sent_ad,
    save_market_ad,
    mark_initialized,
    get_setting,
)

from parser import fetch_ads_playwright
from parser_avby import fetch_ads_avby


check_lock = asyncio.Lock()

_running = False
_thread = None
_loop = None


async def run_check_cycle(send_func=None):

    log("ENTER run_check_cycle")

    running = await get_setting("parser_running", "1")
    if running != "1":
        log("PARSER STOPPED FROM MINI APP")
        return

    if check_lock.locked():
        log("SKIP (already running)")
        return

    async with check_lock:

        filters = await get_all_filters()

        if not filters:
            return

        total_sent = 0

        for (
            filter_id,
            telegram_id,
            source,
            url,
            initialized,
        ) in filters:

            try:

                if source == "kufar":
                    ads = await fetch_ads_playwright(url)
                elif source == "avby":
                    ads = await fetch_ads_avby(url)
                else:
                    ads = []

                log(f"FOUND ADS: {len(ads)}")

                if not initialized:
                    for ad in ads:
                        item_id = ad.get("id")
                        if item_id:
                            await save_sent_ad(filter_id, str(item_id))
                    await mark_initialized(filter_id)
                    continue

                sent_count = 0
                MAX_SEND_PER_CYCLE = 10

                for ad in ads:

                    if sent_count >= MAX_SEND_PER_CYCLE:
                        break

                    item_id = ad.get("id")
                    if not item_id:
                        continue

                    item_id = str(item_id).strip()

                    if await ad_already_sent(filter_id, item_id):
                        continue

                    if send_func is not None:
                        try:
                            await send_func(
                                telegram_id,
                                f"{ad['text']}\n\n{ad['link']}",
                            )
                        except Exception as e:
                            log(f"SEND FAIL {filter_id}: {e}")

                    await save_sent_ad(filter_id, item_id)
                    await save_market_ad(
                        filter_id,
                        item_id,
                        ad["text"],
                        ad.get("price"),
                        ad["link"],
                    )

                    sent_count += 1
                    total_sent += 1

            except Exception as e:
                log(f"ERROR FILTER {filter_id}: {e}")

        if total_sent > 0:
            log(f"SENT: {total_sent}")


async def _scheduler_task():

    global _running

    log("SCHEDULER THREAD STARTED")

    while _running:
        try:
            await run_check_cycle(send_func=None)
        except Exception as e:
            log(f"SCHEDULER ERROR: {e}")

        for _ in range(int(CHECK_INTERVAL)):
            if not _running:
                break
            await asyncio.sleep(1)

    log("SCHEDULER THREAD STOPPED")


def _loop_runner():

    global _loop
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _loop.run_forever()


def start_scheduler():

    global _running, _thread

    if _running:
        log("SCHEDULER ALREADY RUNNING")
        return

    _running = True

    if _thread is None or not _thread.is_alive():
        _thread = threading.Thread(target=_loop_runner, daemon=True)
        _thread.start()

    import time
    time.sleep(0.2)

    asyncio.run_coroutine_threadsafe(_scheduler_task(), _loop)
    log("SCHEDULER START COMMAND SENT")


def stop_scheduler():

    global _running
    _running = False
    log("SCHEDULER STOP COMMAND SENT")
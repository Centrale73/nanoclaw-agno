import asyncio
import os
import logging
from datetime import datetime

import db
from agents.root import run_for_group
from channels.registry import get_active
from scheduler import scheduler_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("orchestrator")

MAX_CONCURRENT = int(os.environ.get("MAX_CONCURRENT_AGENTS", "4"))
semaphore = asyncio.Semaphore(MAX_CONCURRENT)
_group_locks: dict[str, asyncio.Lock] = {}

def group_lock(group_id: str) -> asyncio.Lock:
    if group_id not in _group_locks:
        _group_locks[group_id] = asyncio.Lock()
    return _group_locks[group_id]

async def process_message(msg: dict):
    group_id = msg["group_id"]
    msg_id = msg["id"]
    channel_name = msg["channel"]
    prompt = msg["content"]
    session_id = f"{group_id}:{datetime.now().date()}"
    provider = os.environ.get("ROOT_PROVIDER", "claude-sonnet")

    log.info(f"[{group_id}] Processing: {prompt[:60]}...")

    async with semaphore:
        async with group_lock(group_id):
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, run_for_group, group_id, prompt, session_id, provider
                )
                db.complete(msg_id, response)
                channels = {c.name: c for c in get_active()}
                if channel_name in channels:
                    await channels[channel_name].send(group_id, response)
                log.info(f"[{group_id}] Done.")
            except Exception as e:
                log.error(f"[{group_id}] Error: {e}", exc_info=True)
                db.fail(msg_id, str(e))

async def polling_loop():
    log.info("Polling for messages...")
    while True:
        groups = db.active_groups()
        tasks = []
        for g in groups:
            msg = db.next_pending(g)
            if msg:
                tasks.append(process_message(msg))
        if tasks:
            await asyncio.gather(*tasks)
        else:
            await asyncio.sleep(0.5)

async def main():
    db.init_db()

    # Import channels to trigger self-registration via __init_subclass__
    # Uncomment as needed:
    import channels.telegram   # noqa
    # import channels.discord  # noqa
    # import channels.slack    # noqa

    active = get_active()
    log.info(f"Starting channels: {[c.name for c in active]}")

    await asyncio.gather(
        *[c.start(lambda *a: None) for c in active],
        polling_loop(),
        scheduler_loop(),
    )

if __name__ == "__main__":
    asyncio.run(main())

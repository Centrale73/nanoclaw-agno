import asyncio
import logging
from croniter import croniter
from datetime import datetime
import db

log = logging.getLogger("scheduler")

async def scheduler_loop():
    log.info("Scheduler started.")
    while True:
        now = datetime.now()
        with db.get_conn() as conn:
            tasks = conn.execute("SELECT * FROM scheduled_tasks WHERE enabled=1").fetchall()
        for task in tasks:
            last = datetime.fromisoformat(task["last_run"]) if task["last_run"] else now
            cron = croniter(task["cron"], last)
            if cron.get_next(datetime) <= now:
                log.info(f"Running scheduled task {task['id']} for group {task['group_id']}")
                db.enqueue(task["group_id"], "scheduler", "scheduler", task["prompt"])
                with db.get_conn() as conn:
                    conn.execute(
                        "UPDATE scheduled_tasks SET last_run=? WHERE id=?",
                        (now.isoformat(), task["id"])
                    )
        await asyncio.sleep(30)

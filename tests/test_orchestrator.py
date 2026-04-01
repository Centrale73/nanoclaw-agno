"""Test orchestrator.py — polling loop, group locks, semaphore."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
import orchestrator
import db

db.DB_PATH = "/tmp/test_orchestrator.db"

def cleanup():
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
    orchestrator._group_locks.clear()

def test_group_lock():
    lock1 = orchestrator.group_lock("group_a")
    lock2 = orchestrator.group_lock("group_a")
    lock3 = orchestrator.group_lock("group_b")
    assert lock1 is lock2, "Same group should return same lock"
    assert lock1 is not lock3, "Different groups should have different locks"
    print("  ✓ group_lock returns consistent per-group locks")

def test_semaphore_limit():
    assert orchestrator.semaphore._value <= 10, f"Semaphore too high: {orchestrator.semaphore._value}"
    print(f"  ✓ Semaphore limit = {orchestrator.semaphore._value}")

def test_polling_loop_no_messages():
    """Verify polling loop doesn't crash when queue is empty."""
    cleanup()
    db.init_db()

    async def run_one_cycle():
        groups = db.active_groups()
        assert groups == [], f"Expected no groups, got {groups}"
        # Simulate one polling cycle — no tasks to gather
        tasks = []
        for g in groups:
            msg = db.next_pending(g)
            if msg:
                tasks.append(orchestrator.process_message(msg))
        if tasks:
            await asyncio.gather(*tasks)
        return True

    result = asyncio.run(run_one_cycle())
    assert result is True
    print("  ✓ Polling cycle with empty queue completes without error")

def test_polling_with_pending_messages():
    """Verify messages are picked up correctly (without actually running agents)."""
    cleanup()
    db.init_db()
    db.enqueue("test:poll", "test", "user1", "Hello")
    db.enqueue("test:poll", "test", "user1", "World")
    db.enqueue("test:poll2", "test", "user2", "Different group")

    groups = db.active_groups()
    assert len(groups) == 2, f"Expected 2 groups, got {groups}"

    msg1 = db.next_pending("test:poll")
    assert msg1 is not None
    assert msg1["content"] == "Hello"

    msg2 = db.next_pending("test:poll2")
    assert msg2 is not None
    assert msg2["content"] == "Different group"

    print("  ✓ Messages picked up in correct order across groups")

if __name__ == "__main__":
    print("\n=== orchestrator.py tests ===")
    test_group_lock()
    test_semaphore_limit()
    test_polling_loop_no_messages()
    test_polling_with_pending_messages()
    cleanup()
    print("=== ALL orchestrator.py TESTS PASSED ===\n")

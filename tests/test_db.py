"""Test db.py — SQLite message queue operations."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import db

# Use an in-memory-like temp file so tests are isolated
db.DB_PATH = "/tmp/test_nanoclaw.db"

def cleanup():
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)

def test_init_and_enqueue():
    cleanup()
    db.init_db()

    # Enqueue two messages in different groups
    id1 = db.enqueue("telegram:111", "telegram", "user_a", "Hello world")
    id2 = db.enqueue("telegram:222", "telegram", "user_b", "Second message")
    id3 = db.enqueue("telegram:111", "telegram", "user_a", "Follow-up")

    assert id1 == 1, f"Expected id 1, got {id1}"
    assert id2 == 2, f"Expected id 2, got {id2}"
    assert id3 == 3, f"Expected id 3, got {id3}"
    print("  ✓ enqueue works, returns incrementing IDs")

def test_active_groups():
    groups = db.active_groups()
    assert set(groups) == {"telegram:111", "telegram:222"}, f"Got {groups}"
    print("  ✓ active_groups returns groups with pending messages")

def test_next_pending():
    msg = db.next_pending("telegram:111")
    assert msg is not None
    assert msg["content"] == "Hello world"
    assert msg["status"] == "pending"  # was pending when read, now processing in DB
    print(f"  ✓ next_pending returns oldest pending (id={msg['id']})")

    # Verify it's now 'processing' in DB
    with db.get_conn() as conn:
        row = conn.execute("SELECT status FROM messages WHERE id=?", (msg["id"],)).fetchone()
        assert row["status"] == "processing", f"Expected 'processing', got {row['status']}"
    print("  ✓ message status updated to 'processing'")

def test_complete():
    db.complete(1, "Response to hello")
    with db.get_conn() as conn:
        row = conn.execute("SELECT status, response FROM messages WHERE id=1").fetchone()
        assert row["status"] == "done"
        assert row["response"] == "Response to hello"
    print("  ✓ complete() sets status='done' and stores response")

def test_fail():
    db.fail(2, "Provider timeout")
    with db.get_conn() as conn:
        row = conn.execute("SELECT status, response FROM messages WHERE id=2").fetchone()
        assert row["status"] == "error"
        assert row["response"] == "Provider timeout"
    print("  ✓ fail() sets status='error' and stores error message")

def test_next_pending_order():
    # Message 1 is done, message 3 should be next for group telegram:111
    msg = db.next_pending("telegram:111")
    assert msg is not None
    assert msg["id"] == 3, f"Expected id 3, got {msg['id']}"
    assert msg["content"] == "Follow-up"
    print("  ✓ next_pending returns correct order after first is completed")

def test_next_pending_empty():
    # Group telegram:222's only message (id=2) was failed, so no pending
    msg = db.next_pending("telegram:222")
    assert msg is None
    print("  ✓ next_pending returns None when no pending messages")

def test_active_groups_after_processing():
    # Complete message 3 — telegram:111 should have no more pending
    db.complete(3, "Done")
    groups = db.active_groups()
    assert groups == [], f"Expected empty, got {groups}"
    print("  ✓ active_groups empty after all messages processed")

if __name__ == "__main__":
    print("\n=== db.py tests ===")
    test_init_and_enqueue()
    test_active_groups()
    test_next_pending()
    test_complete()
    test_fail()
    test_next_pending_order()
    test_next_pending_empty()
    test_active_groups_after_processing()
    cleanup()
    print("=== ALL db.py TESTS PASSED ===\n")

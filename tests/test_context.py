"""Test context.py — per-group context read/write/update."""
import sys, os, shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import context

# Override GROUPS_DIR to a temp location
context.GROUPS_DIR = __import__("pathlib").Path("/tmp/test_groups")

def cleanup():
    if context.GROUPS_DIR.exists():
        shutil.rmtree(context.GROUPS_DIR)

def test_load_empty():
    cleanup()
    result = context.load_context("telegram:999")
    assert result == "", f"Expected empty string, got '{result}'"
    print("  ✓ load_context returns '' for non-existent group")

def test_save_and_load():
    context.save_context("telegram:999", "# Group Notes\nThis is a test group.")
    result = context.load_context("telegram:999")
    assert "This is a test group." in result
    print("  ✓ save_context + load_context roundtrip works")

def test_context_path_sanitization():
    path = context.context_path("telegram:123")
    assert ":" not in str(path.name), f"Colon in path: {path}"
    assert "telegram_123" in str(path)
    print(f"  ✓ context_path sanitizes colons → {path}")

def test_update_context_new_key():
    context.update_context("telegram:999", "Preferences", "User prefers concise answers")
    result = context.load_context("telegram:999")
    assert "## Preferences" in result
    assert "User prefers concise answers" in result
    print("  ✓ update_context appends new key")

def test_update_context_replace_key():
    context.update_context("telegram:999", "Preferences", "User prefers detailed answers")
    result = context.load_context("telegram:999")
    assert "User prefers detailed answers" in result
    # Old value should be gone
    assert "concise" not in result
    print("  ✓ update_context replaces existing key")

def test_update_context_multiple_keys():
    context.update_context("telegram:999", "Language", "French")
    result = context.load_context("telegram:999")
    assert "## Preferences" in result
    assert "## Language" in result
    assert "French" in result
    assert "detailed answers" in result
    print("  ✓ multiple keys coexist in context")

def test_group_isolation():
    context.save_context("discord:777", "Discord group context")
    r1 = context.load_context("telegram:999")
    r2 = context.load_context("discord:777")
    assert "Discord" not in r1
    assert "Discord" in r2
    print("  ✓ different group_ids are fully isolated")

if __name__ == "__main__":
    print("\n=== context.py tests ===")
    test_load_empty()
    test_save_and_load()
    test_context_path_sanitization()
    test_update_context_new_key()
    test_update_context_replace_key()
    test_update_context_multiple_keys()
    test_group_isolation()
    cleanup()
    print("=== ALL context.py TESTS PASSED ===\n")

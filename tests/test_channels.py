"""Test channels/registry.py — self-registration pattern."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from channels.registry import BaseChannel, get_active, _registry

def test_self_registration():
    # Clear any prior registrations
    _registry.clear()

    class TestChannel(BaseChannel):
        name = "test_channel"

        async def start(self, on_message):
            pass

        async def send(self, group_id, text):
            pass

    active = get_active()
    names = [c.name for c in active]
    assert "test_channel" in names, f"Expected 'test_channel' in {names}"
    print(f"  ✓ TestChannel self-registered: {names}")

def test_multiple_channels():
    _registry.clear()

    class Chan1(BaseChannel):
        name = "chan1"
        async def start(self, on_message): pass
        async def send(self, group_id, text): pass

    class Chan2(BaseChannel):
        name = "chan2"
        async def start(self, on_message): pass
        async def send(self, group_id, text): pass

    active = get_active()
    names = [c.name for c in active]
    assert "chan1" in names and "chan2" in names, f"Got {names}"
    print(f"  ✓ Multiple channels registered: {names}")

def test_abstract_methods_enforced():
    try:
        class BadChannel(BaseChannel):
            name = "bad"
            # Missing start() and send()

        # Instantiation should fail
        BadChannel()
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "abstract" in str(e).lower() or "instantiate" in str(e).lower()
    print("  ✓ Abstract methods enforced (can't instantiate without start/send)")

    _registry.pop("bad", None)  # clean up

if __name__ == "__main__":
    print("\n=== channels/registry.py tests ===")
    test_self_registration()
    test_multiple_channels()
    test_abstract_methods_enforced()
    print("=== ALL channels/registry.py TESTS PASSED ===\n")

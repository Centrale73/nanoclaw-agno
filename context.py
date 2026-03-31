from pathlib import Path

GROUPS_DIR = Path("groups")

def context_path(group_id: str) -> Path:
    safe = group_id.replace(":", "_")
    return GROUPS_DIR / safe / "context.md"

def load_context(group_id: str) -> str:
    path = context_path(group_id)
    return path.read_text() if path.exists() else ""

def save_context(group_id: str, content: str):
    path = context_path(group_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

def update_context(group_id: str, key: str, value: str):
    path = context_path(group_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    current = path.read_text() if path.exists() else ""
    marker = f"## {key}"
    if marker in current:
        lines = current.split("\n")
        out, skip = [], False
        for line in lines:
            if line.startswith(marker):
                out.append(f"{marker}\n{value}")
                skip = True
            elif skip and line.startswith("## "):
                skip = False
                out.append(line)
            elif not skip:
                out.append(line)
        path.write_text("\n".join(out))
    else:
        with path.open("a") as f:
            f.write(f"\n{marker}\n{value}\n")

from pathlib import Path

WORKSPACE = Path("workspace")


def list_files():
    return [f.name for f in WORKSPACE.iterdir()]


def read_file(name):
    return (WORKSPACE / name).read_text(encoding="utf-8")


if __name__ == "__main__":
    print(list_files())
    print(read_file("meeting-notes.txt"))
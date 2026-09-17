#!/usr/bin/python3
"""Create the three scoped release roadmap issues with GitHub CLI."""

import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPO = "YidaHao/SessionGlow"


def gh(*args):
    return subprocess.check_output(["gh", *args], text=True, cwd=ROOT)


def main():
    gh("label", "create", "help wanted", "--repo", REPO, "--color", "008672", "--force")
    gh("label", "create", "good first issue", "--repo", REPO, "--color", "7057ff", "--force")
    existing = json.loads(gh("issue", "list", "--repo", REPO, "--state", "all", "--limit", "100", "--json", "title,url"))
    titles = {item["title"] for item in existing}
    for name in ("wayland", "appimage", "localization"):
        path = ROOT / "docs/roadmap" / f"{name}.md"
        title = path.read_text().splitlines()[0].removeprefix("# ")
        if title in titles:
            continue
        args = ["issue", "create", "--repo", REPO, "--title", title, "--body-file", str(path), "--label", "help wanted"]
        if name == "localization":
            args.extend(["--label", "good first issue"])
        print(gh(*args).strip())


if __name__ == "__main__":
    main()

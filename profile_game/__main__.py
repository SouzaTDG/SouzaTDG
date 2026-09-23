"""Uso: python -m profile_game [--demo] [--out dist]   (token em GH_TOKEN)."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from .config import CONFIG
from .data import demo_grid, demo_languages, fetch_calendar, fetch_language_frame, language_slices
from .planner import plan_game, validate_plan
from .render import render_svg


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="dados simulados, sem token")
    parser.add_argument("--out", default="dist")
    args = parser.parse_args(argv)

    if args.demo:
        counts, total = demo_grid()
        frame = demo_languages()
    else:
        token = os.environ["GH_TOKEN"]
        counts, total = fetch_calendar(token)
        frame = fetch_language_frame(token)

    plan = plan_game(counts, CONFIG["game"])
    validate_plan(plan)
    slices = language_slices(frame, CONFIG)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, theme in CONFIG["themes"].items():
        (out / f"bomberman-{name}.svg").write_text(render_svg(plan, total, slices, CONFIG, theme), encoding="utf-8")

    print(f"bombas={len(plan.bombs)} escudos={len(plan.shields)} restantes={plan.leftover} "
          f"duração={plan.duration:.0f}s contribuições={total}")


if __name__ == "__main__":
    main()

"""Renderização do SVG animado (SMIL, sem JavaScript: funciona em <img> no README)."""
from __future__ import annotations

import math
from xml.sax.saxutils import escape

from .planner import Plan

FONT = 'ui-monospace, SFMono-Regular, Menlo, Consolas, "Courier New", monospace'


def _discrete(attr: str, values: list[str], ticks: list[int], plan: Plan) -> str:
    keys = ";".join(f"{t / plan.total_ticks:.5f}" for t in ticks)
    return (f'<animate attributeName="{attr}" values="{";".join(values)}" keyTimes="{keys}" '
            f'calcMode="discrete" dur="{plan.duration:.2f}s" repeatCount="indefinite"/>')


def _toggle(intervals: list[tuple[int, int]], plan: Plan) -> str:
    """Opacidade 0/1 discreta: visível apenas nos intervalos [início, fim] (em ticks)."""
    values, ticks = [], []
    if not intervals or intervals[0][0] > 0:
        values.append("0"); ticks.append(0)
    for start, end in intervals:
        values += ["1", "0"]; ticks += [start, min(end, plan.total_ticks)]
    return _discrete("opacity", values, ticks, plan)


def _hero(th: dict) -> str:
    return (
        f'<circle cx="7" cy="6" r="5.4" fill="{th["hero_head"]}"/>'
        f'<rect x="3.2" y="4" width="7.6" height="4.6" rx="2" fill="{th["hero_face"]}"/>'
        '<circle cx="5.3" cy="6.2" r=".85" fill="#222"/><circle cx="8.7" cy="6.2" r=".85" fill="#222"/>'
        f'<rect x="3" y="9.6" width="8" height="4.4" rx="1.6" fill="{th["hero_body"]}"/>'
        '<rect x="6.6" y="-.6" width=".8" height="1.6" fill="#fff"/>'
        '<circle cx="7" cy="-1" r="1.5" fill="#ff5fa2"/>'
    )


BOMB = (
    '<circle cx="7" cy="8.2" r="5" fill="#111" stroke="#777" stroke-width=".6"/>'
    '<circle cx="5.2" cy="6.6" r="1.1" fill="#fff" opacity=".35"/>'
    '<path d="M9.6 4 L11.2 2.4" stroke="#c9a66b" stroke-width="1.3" fill="none"/>'
    '<circle cx="11.6" cy="2" r="1.4" fill="#ffb703"/>'
)


def _donut(slices, cx: float, cy: float, th: dict, radius: float = 27, width: float = 13) -> str:
    circ = 2 * math.pi * radius
    out = [f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{th["bar_bg"]}" stroke-width="{width}"/>']
    offset = 0.0
    for _, pct, color in slices:
        length = circ * pct / 100
        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'stroke-dasharray="{length:.2f} {circ - length:.2f}" stroke-dashoffset="{-offset:.2f}" '
            f'transform="rotate(-90 {cx} {cy})"/>'
        )
        offset += length
    return "".join(out)


def render_svg(plan: Plan, total_contrib: int, slices, cfg: dict, th: dict) -> str:
    lay, txt = cfg["layout"], cfg["text"]
    cell, gap = lay["cell"], lay["gap"]
    pitch = cell + gap
    rows, cols = plan.shape
    mx, my = lay["margin_x"], lay["margin_top"]
    width = 2 * mx + cols * pitch - gap
    grid_h = rows * pitch - gap
    hud_y = my + grid_h + 24
    height = hud_y + lay["hud_height"]

    def X(c): return mx + c * pitch
    def Y(r): return my + r * pitch

    css = (f".f{{fill:{th['floor']}}}"
           + "".join(f".l{i + 1}{{fill:{col}}}" for i, col in enumerate(th["levels"]))
           + f"text{{font-family:{FONT};fill:{th['text']}}}")
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" '
        f'aria-label="{escape(txt["alt"])}">',
        f"<style>{css}</style>",
        f'<defs><rect id="c" width="{cell}" height="{cell}" rx="3"/></defs>',
        f'<rect width="{width}" height="{height}" rx="8" fill="{th["bg"]}"/>',
        f'<text x="{mx}" y="26" font-size="13" font-weight="700" letter-spacing="1">{escape(txt["title"])}</text>',
        f'<text x="{width - mx}" y="26" font-size="12" text-anchor="end" style="fill:{th["muted"]}">'
        f'{escape(txt["contributions"].format(n=total_contrib))}</text>',
    ]

    # chão
    for r in range(rows):
        for c in range(cols):
            if plan.exists[r, c]:
                p.append(f'<use xlink:href="#c" class="f" x="{X(c)}" y="{Y(r)}"/>')

    # blocos (animam opacidade e, se resistentes, a cor após o 1º impacto)
    for r in range(rows):
        for c in range(cols):
            if plan.hp0[r, c] <= 0:
                continue
            anims = []
            for tick, left in plan.events.get((r, c), []):
                if left == 0:
                    anims.append(_discrete("opacity", ["1", "0"], [0, tick], plan))
                else:
                    anims.append(_discrete("fill", [th["levels"][plan.levels[r, c] - 1], th["cracked"]], [0, tick], plan))
            p.append(f'<use xlink:href="#c" class="l{plan.levels[r, c]}" x="{X(c)}" y="{Y(r)}">{"".join(anims)}</use>')

    # bombas
    for b in plan.bombs:
        p.append(f'<g transform="translate({X(b.cell[1])} {Y(b.cell[0])})" opacity="0">'
                 f'{_toggle([(b.place, b.explode)], plan)}{BOMB}</g>')

    # herói (+ escudo quando não há rota de fuga)
    values = ";".join(f"{X(c)} {Y(r)}" for r, c in plan.path)
    r0, c0 = plan.path[0]
    shield = ""
    if plan.shields:
        shield = (f'<circle cx="7" cy="7" r="10" fill="{th["hero_body"]}" fill-opacity=".25" '
                  f'stroke="{th["hero_body"]}" stroke-width="1.2" opacity="0">{_toggle(plan.shields, plan)}</circle>')
    p.append(
        f'<g transform="translate({X(c0)} {Y(r0)})">'
        f'<animateTransform attributeName="transform" type="translate" calcMode="linear" values="{values}" '
        f'dur="{plan.duration:.2f}s" repeatCount="indefinite"/>{_hero(th)}{shield}</g>'
    )

    # chamas
    for b in plan.bombs:
        shapes = "".join(
            f'<rect x="{X(c) - 1}" y="{Y(r) - 1}" width="{cell + 2}" height="{cell + 2}" rx="4" fill="{th["flame_outer"]}"/>'
            f'<rect x="{X(c) + 3}" y="{Y(r) + 3}" width="{cell - 6}" height="{cell - 6}" rx="2" fill="{th["flame_inner"]}"/>'
            for r, c in b.flames
        )
        p.append(f'<g opacity="0">{_toggle([(b.explode, b.explode + 1)], plan)}{shapes}</g>')

    # HUD: donut de linguagens
    cy = hud_y + 46
    if slices:
        p.append(_donut(slices, mx + 34, cy, th))
        for i, (name, pct, color) in enumerate(slices):
            lx, ly = mx + 92 + (i // 3) * 165, hud_y + 26 + (i % 3) * 20
            p.append(f'<rect x="{lx}" y="{ly - 9}" width="10" height="10" rx="2" fill="{color}"/>'
                     f'<text x="{lx + 16}" y="{ly}" font-size="12">{escape(name)} {pct:.0f}%</text>')

    # HUD: progresso (hp removido / hp total)
    bar_w = 240
    bar_x, bar_y = width - mx - bar_w, hud_y + 40
    total_hp = int(plan.hp0.sum())
    by_tick: dict[int, int] = {}
    for evs in plan.events.values():
        for tick, _ in evs:
            by_tick[tick] = by_tick.get(tick, 0) + 1
    ticks, widths, done = [0], ["0"], 0
    for tick in sorted(by_tick):
        done += by_tick[tick]
        ticks.append(tick)
        widths.append(f"{bar_w * done / max(total_hp, 1):.1f}")
    p.append(f'<text x="{bar_x}" y="{bar_y - 8}" font-size="12" style="fill:{th["muted"]}">{escape(txt["progress"])}</text>')
    p.append(f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="12" rx="6" fill="{th["bar_bg"]}"/>')
    p.append(f'<rect x="{bar_x}" y="{bar_y}" width="0" height="12" rx="6" fill="{th["bar_fg"]}">'
             f'{_discrete("width", widths, ticks, plan)}</rect>')

    # STAGE CLEAR durante a pausa final
    clear_tick = plan.bombs[-1].explode + 1 if plan.bombs else 0
    p.append(
        f'<text x="{width / 2}" y="{my + grid_h / 2 + 8}" font-size="26" font-weight="700" text-anchor="middle" '
        f'letter-spacing="2" opacity="0" style="fill:{th["accent"]}">'
        f'{escape(txt["clear"])}{_toggle([(clear_tick, plan.total_ticks)], plan)}</text>'
    )
    p.append("</svg>")
    return "".join(p)

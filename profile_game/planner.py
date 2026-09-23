"""Planejamento do jogo (lógica fixa). Toda regra ajustável vem do dicionário `game` do CONFIG."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass

import numpy as np

STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))  # (dlinha, dcoluna)
Cell = tuple[int, int]                       # (linha, coluna)


@dataclass
class Bomb:
    cell: Cell
    place: int
    explode: int
    flames: list[Cell]
    shielded: bool = False                     # sem rota de fuga: o herói usa o escudo


@dataclass
class Plan:
    levels: np.ndarray                         # nível 0-4 por célula
    hp0: np.ndarray                            # resistência inicial dos blocos
    exists: np.ndarray                         # célula existe no calendário
    path: list[Cell]                           # posição do herói a cada tick
    bombs: list[Bomb]
    events: dict[Cell, list[tuple[int, int]]]  # célula -> [(tick, hp restante)]
    shields: list[tuple[int, int]]             # intervalos [tick, tick] com escudo ativo
    tick_seconds: float
    leftover: int                              # blocos que não deu para destruir

    @property
    def shape(self) -> tuple[int, int]:
        return self.levels.shape

    @property
    def total_ticks(self) -> int:
        return len(self.path) - 1

    @property
    def duration(self) -> float:
        return self.total_ticks * self.tick_seconds


def build_grid(counts: np.ndarray, game: dict):
    """Contagens -> níveis (quartis das células ativas), resistência e máscara de existência."""
    exists = ~np.isnan(counts)
    filled = np.nan_to_num(counts, nan=0.0)
    levels = np.zeros(filled.shape, dtype=int)
    active = filled > 0
    if active.any():
        cuts = np.quantile(filled[active], [0.25, 0.5, 0.75])
        levels[active] = np.digitize(filled[active], cuts, right=True) + 1
    hp = np.where(levels > 0, 1, 0)
    hp[levels == game["heavy_level"]] = game["heavy_hp"]
    return levels, hp, exists


def pick_spawn(exists: np.ndarray, hp: np.ndarray) -> Cell:
    """Célula da coluna 0 com maior área livre alcançável (desempate: mais central)."""
    free = exists & (hp == 0)
    mid = exists.shape[0] // 2
    best = None
    for r in np.nonzero(exists[:, 0])[0]:
        passable = free.copy()
        passable[r, 0] = True
        area = int((bfs((int(r), 0), passable)[0] >= 0).sum())
        key = (area, -abs(int(r) - mid))
        if best is None or key > best[0]:
            best = (key, (int(r), 0))
    return best[1]


def bfs(start: Cell, passable: np.ndarray, limit: int | None = None):
    rows, cols = passable.shape
    dist = np.full((rows, cols), -1, dtype=int)
    prev: dict[Cell, Cell] = {}
    dist[start] = 0
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        d = dist[r, c]
        if limit is not None and d >= limit:
            continue
        for dr, dc in STEPS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and passable[nr, nc] and dist[nr, nc] < 0:
                dist[nr, nc] = d + 1
                prev[(nr, nc)] = (r, c)
                queue.append((nr, nc))
    return dist, prev


def path_to(prev: dict[Cell, Cell], start: Cell, goal: Cell) -> list[Cell]:
    route = [goal]
    while route[-1] != start:
        route.append(prev[route[-1]])
    return route[::-1]


def blast(hp: np.ndarray, exists: np.ndarray, cell: Cell, reach: int):
    """Explosão em cruz: para no primeiro bloco de cada direção (que é atingido)."""
    rows, cols = hp.shape
    flames, hits = [cell], []
    for dr, dc in STEPS:
        for k in range(1, reach + 1):
            r, c = cell[0] + dr * k, cell[1] + dc * k
            if not (0 <= r < rows and 0 <= c < cols) or not exists[r, c]:
                break
            flames.append((r, c))
            if hp[r, c] > 0:
                hits.append((r, c))
                break
    return flames, hits


def find_escape(cell: Cell, walk: np.ndarray, danger: set[Cell], fuse: int) -> list[Cell] | None:
    """Menor rota (<= pavio) até uma célula fora da explosão; None se o herói morreria."""
    dist, prev = bfs(cell, walk, limit=fuse)
    best = None
    for r, c in zip(*np.nonzero(dist > 0)):
        if (int(r), int(c)) not in danger and (best is None or dist[r, c] < best[0]):
            best = (int(dist[r, c]), (int(r), int(c)))
    return path_to(prev, cell, best[1])[1:] if best else None


def plan_game(counts: np.ndarray, game: dict) -> Plan:
    levels, hp0, exists = build_grid(counts, game)
    spawn = pick_spawn(exists, hp0)
    levels[spawn], hp0[spawn] = 0, 0          # a casa do herói é sempre chão livre
    hp = hp0.copy()
    reach, fuse = game["blast_range"], game["fuse_ticks"]

    pos, path = spawn, [spawn]
    bombs: list[Bomb] = []
    shields: list[tuple[int, int]] = []
    events: dict[Cell, list[tuple[int, int]]] = defaultdict(list)
    last_flames: set[Cell] = set()

    while hp.any():
        walk = exists & (hp == 0)
        dist, prev = bfs(pos, walk)
        cands = []
        for r, c in zip(*np.nonzero(dist >= 0)):
            cell = (int(r), int(c))
            flames, hits = blast(hp, exists, cell, reach)
            if hits:
                d = int(dist[cell])
                cands.append((len(hits) / (d + fuse), -d, cell, flames, hits))
        cands.sort(key=lambda x: (x[0], x[1]), reverse=True)

        chosen = None
        for _, _, cell, flames, hits in cands[: game["candidates_checked"]]:
            escape = find_escape(cell, walk, set(flames), fuse)
            if escape is not None:
                chosen = (cell, flames, hits, escape)
                break
        shielded = False
        if chosen is None:
            if not cands:
                break
            _, _, cell, flames, hits = cands[0]   # sem fuga possível: escudo
            chosen, shielded = (cell, flames, hits, []), True

        cell, flames, hits, escape = chosen
        route = path_to(prev, pos, cell)
        first_step = route[1] if len(route) > 1 else (escape[0] if escape else None)
        if first_step in last_flames:
            path.append(pos)                   # espera as chamas anteriores apagarem
        path.extend(route[1:])
        place = len(path) - 1
        path.extend(escape)
        explode = place + fuse
        while len(path) - 1 < explode:
            path.append(path[-1])
        bombs.append(Bomb(cell, place, explode, flames, shielded))
        if shielded:
            shields.append((place, explode + 1))
        for h in hits:
            hp[h] -= 1
            events[h].append((explode, int(hp[h])))
        last_flames, pos = set(flames), path[-1]

    path.extend([pos] * game["hold_ticks"])
    ticks = max(len(path) - 1, 1)
    tick_seconds = float(np.clip(game["target_seconds"] / ticks,
                                 game["tick_seconds_min"], game["tick_seconds_max"]))
    return Plan(levels, hp0, exists, path, bombs, dict(events), shields, tick_seconds, int(hp.astype(bool).sum()))


def validate_plan(plan: Plan) -> None:
    """Invariantes: falha o workflow em vez de publicar uma animação incoerente."""
    hp = plan.hp0.copy()
    by_tick: dict[int, list[Cell]] = defaultdict(list)
    for cell, evs in plan.events.items():
        for tick, _ in evs:
            by_tick[tick].append(cell)
    bomb_at = {b.explode: b for b in plan.bombs}
    for t, pos in enumerate(plan.path):
        for cell in by_tick.get(t, []):
            hp[cell] -= 1
        assert plan.exists[pos], f"tick {t}: herói fora do mapa"
        assert hp[pos] == 0, f"tick {t}: herói dentro de um bloco"
        if t > 0:
            prev = plan.path[t - 1]
            assert abs(prev[0] - pos[0]) + abs(prev[1] - pos[1]) <= 1, f"tick {t}: salto"
        bomb = bomb_at.get(t)
        if bomb and not bomb.shielded:
            assert pos not in bomb.flames, f"tick {t}: herói na explosão"
            nxt = plan.path[min(t + 1, len(plan.path) - 1)]
            assert nxt not in bomb.flames, f"tick {t + 1}: herói entrou nas chamas"

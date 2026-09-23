"""Camada de dados: GitHub GraphQL -> arrays/DataFrames. Sem regras de jogo aqui."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import requests

API = "https://api.github.com/graphql"

CALENDAR_Q = """
query {
  viewer {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount weekday } }
      }
    }
  }
}
"""

REPOS_Q = """
query($since: GitTimestamp!, $author: CommitAuthor!, $after: String) {
  viewer {
    repositories(first: 100, after: $after, ownerAffiliations: OWNER, isFork: false) {
      pageInfo { hasNextPage endCursor }
      nodes {
        nameWithOwner
        isPrivate
        primaryLanguage { name }
        defaultBranchRef {
          target { ... on Commit { history(since: $since, author: $author) { totalCount } } }
        }
      }
    }
  }
}
"""


def gql(token: str, query: str, variables: dict | None = None) -> dict:
    resp = requests.post(
        API,
        json={"query": query, "variables": variables or {}},
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json()
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload["data"]


def fetch_calendar(token: str) -> tuple[np.ndarray, int]:
    """Retorna (contagens[7, semanas] com NaN onde não há dia, total do ano).

    O calendário já inclui as contribuições privadas (contadas de forma anônima).
    """
    cal = gql(token, CALENDAR_Q)["viewer"]["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    grid = np.full((7, len(weeks)), np.nan)
    for w, week in enumerate(weeks):
        for day in week["contributionDays"]:
            grid[day["weekday"], w] = day["contributionCount"]
    return grid, int(cal["totalContributions"])


def fetch_language_frame(token: str, days: int = 365) -> pd.DataFrame:
    """Commits por repositório na branch padrão, com a linguagem primária (inclui privados)."""
    viewer_id = gql(token, "query { viewer { id } }")["viewer"]["id"]
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows, after = [], None
    while True:
        data = gql(token, REPOS_Q, {"since": since, "author": {"id": viewer_id}, "after": after})
        page = data["viewer"]["repositories"]
        for node in page["nodes"]:
            target = (node["defaultBranchRef"] or {}).get("target") or {}
            rows.append({
                "repo": node["nameWithOwner"],
                "private": node["isPrivate"],
                "lang": (node["primaryLanguage"] or {}).get("name"),
                "commits": target.get("history", {}).get("totalCount", 0),
            })
        if not page["pageInfo"]["hasNextPage"]:
            break
        after = page["pageInfo"]["endCursor"]
    return pd.DataFrame(rows)


def language_slices(df: pd.DataFrame, cfg: dict) -> list[tuple[str, float, str]]:
    """DataFrame -> [(linguagem, %, cor)] já filtrado, agrupado e ordenado."""
    lc = cfg["languages"]
    df = df[~df["repo"].isin(lc["ignore_repos"]) & df["lang"].notna() & (df["commits"] > 0)].copy()
    df["lang"] = df["lang"].replace(lc["aliases"])
    df = df[~df["lang"].isin(lc["ignore_langs"])]
    totals = df.groupby("lang")["commits"].sum().sort_values(ascending=False)
    if totals.empty:
        return []
    head, tail = totals.iloc[: lc["max_slices"]], totals.iloc[lc["max_slices"]:]
    if tail.sum() > 0:
        head = pd.concat([head, pd.Series({lc["other_label"]: tail.sum()})])
    pct = head / head.sum() * 100
    return [(name, float(p), lc["colors"].get(name, lc["fallback_color"])) for name, p in pct.items()]


# --- dados simulados (teste local sem token) -------------------------------------------------

def demo_grid(seed: int = 7, weeks: int = 53) -> tuple[np.ndarray, int]:
    rng = np.random.default_rng(seed)
    active = rng.random((7, weeks)) < np.where(np.arange(7)[:, None] % 6 == 0, 0.12, 0.30)
    grid = (active * rng.integers(1, 12, (7, weeks))).astype(float)
    grid[:3, 0] = np.nan          # semana inicial incompleta
    grid[4:, -1] = np.nan         # semana atual incompleta
    return grid, int(np.nansum(grid))


def demo_languages() -> pd.DataFrame:
    rows = [
        ("A/meu-portfolio", "Svelte", 18), ("A/rpa_jusia_fluid", "Python", 13),
        ("A/site-casamento", "HTML", 12), ("A/rpa_elaw", "Python", 6),
        ("A/bot_fluid_rpa", "HTML", 6), ("A/ProcessoCNJ", "HTML", 5),
        ("A/viana_assessoria", "Svelte", 4), ("A/CustasSync", "Python", 4),
        ("SouzaTDG/SouzaTDG", None, 14),
    ]
    return pd.DataFrame(rows, columns=["repo", "lang", "commits"])

"""Regras voláteis: tudo o que pode mudar sem tocar na lógica de processamento."""

CONFIG = {
    "game": {
        "blast_range": 2,          # alcance da explosão em cruz (células)
        "fuse_ticks": 3,           # tempo do pavio (1 tick = 1 passo do herói)
        "heavy_level": 4,          # nível de contribuição que vira bloco resistente
        "heavy_hp": 2,             # bombas necessárias para destruir o bloco resistente
        "hold_ticks": 12,          # pausa no fim (mostra "STAGE CLEAR") antes de reiniciar
        "target_seconds": 45,      # duração desejada do loop
        "tick_seconds_min": 0.06,  # limites de velocidade do herói
        "tick_seconds_max": 0.20,
        "candidates_checked": 60,  # quantas posições de bomba testar por rodada
    },
    "languages": {
        "ignore_repos": {"SouzaTDG/SouzaTDG"},  # repositório do perfil (só arquivos gerados)
        "ignore_langs": set(),
        "aliases": {},                          # ex.: {"Jupyter Notebook": "Python"}
        "colors": {
            "Python": "#3572A5",
            "Svelte": "#ff3e00",
            "HTML": "#e34c26",
            "JavaScript": "#f1e05a",
            "TypeScript": "#3178c6",
            "CSS": "#563d7c",
            "Shell": "#89e051",
        },
        "fallback_color": "#8b949e",
        "max_slices": 5,
        "other_label": "Outras",
    },
    "layout": {"cell": 14, "gap": 3, "margin_x": 24, "margin_top": 44, "hud_height": 104},
    "text": {
        "title": "BOMBERMAN CONTRIBUTIONS",
        "contributions": "{n} contribuições no último ano",
        "progress": "BLOCOS",
        "clear": "STAGE CLEAR!",
        "alt": "Bomberman destruindo o calendário de contribuições",
    },
    "themes": {
        "dark": {
            "bg": "#0d1117", "floor": "#161b22",
            "levels": ["#0e4429", "#006d32", "#26a641", "#39d353"],
            "cracked": "#238636",
            "text": "#e6edf3", "muted": "#8b949e",
            "bar_bg": "#21262d", "bar_fg": "#39d353", "accent": "#ffd33d",
            "hero_head": "#ffffff", "hero_face": "#ffd9b3", "hero_body": "#2f6fed",
            "flame_outer": "#ff7b00", "flame_inner": "#ffe066",
        },
        "light": {
            "bg": "#ffffff", "floor": "#ebedf0",
            "levels": ["#9be9a8", "#40c463", "#30a14e", "#216e39"],
            "cracked": "#40c463",
            "text": "#1f2328", "muted": "#59636e",
            "bar_bg": "#d0d7de", "bar_fg": "#30a14e", "accent": "#bf8700",
            "hero_head": "#ffffff", "hero_face": "#ffd9b3", "hero_body": "#2f6fed",
            "flame_outer": "#ff7b00", "flame_inner": "#ffe066",
        },
    },
}

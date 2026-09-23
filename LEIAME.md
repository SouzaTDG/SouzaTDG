# Bomberman contribution graph

Gera dois SVGs animados (`bomberman-dark.svg` e `bomberman-light.svg`) a partir do calendário de
contribuições (inclui as privadas) e dos commits por linguagem (inclui repositórios privados).

- Teste local sem token: `python -m profile_game --demo --out dist`
- Teste local real: defina `GH_TOKEN` e rode `python -m profile_game --out dist`
- Regras ajustáveis (alcance da bomba, pavio, blocos resistentes, cores, repositórios ignorados):
  `profile_game/config.py`

## No README do perfil

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/SouzaTDG/SouzaTDG/output/bomberman-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/SouzaTDG/SouzaTDG/output/bomberman-light.svg">
  <img alt="Bomberman destruindo o calendário de contribuições" src="https://raw.githubusercontent.com/SouzaTDG/SouzaTDG/output/bomberman-dark.svg">
</picture>
```

# REAL_DATA_TODO.md
Úkoly pro integraci skutečných dat MS 2026 do aplikace

Tento dokument obsahuje kompletní TODO checklist, který je potřeba splnit, aby aplikace uměla načítat a používat skutečná data MS 2026 (týmy, skupiny, zápasy, predikce).

---

# ✅ 1. Příprava datové struktury

## [ ] Vytvořit složku `backend/data/`
## [ ] Přidat prázdný soubor `teams_ms2026.json`
## [ ] Přidat prázdný soubor `matches_ms2026.json`

---

# ✅ 2. Implementace importní logiky

## [ ] Vytvořit soubor `backend/app/data_loader.py`
Obsahuje funkce:
- [ ] `load_teams_from_json()`
- [ ] `load_matches_from_json()`
- [ ] `recompute_predictions()`

## [ ] Otestovat, že import týmů funguje
## [ ] Otestovat, že import zápasů funguje
## [ ] Otestovat, že přepočet predikcí funguje

---

# ✅ 3. Admin API endpointy

V souboru `backend/app/routers/admin.py`:

## [ ] `/admin/load-teams`
## [ ] `/admin/load-matches`
## [ ] `/admin/recompute-predictions`

V `main.py`:

## [ ] `app.include_router(admin.router, prefix="/api/v1/admin")`

---

# ✅ 4. JSON šablony pro skutečná data

## [ ] Definovat strukturu `teams_ms2026.json`
```json
[
  {
    "name": "",
    "fifa_code": "",
    "group": "",
    "rating_attack": 0.0,
    "rating_defense": 0.0,
    "rating_overall": 0.0
  }
]

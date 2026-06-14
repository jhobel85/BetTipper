# REAL_DATA_FEATURES.md
Complete Description of All New Features in the MS 2026 Prediction System

This document summarizes all new modules, algorithms, and features added to the prediction system.  
It now functions as a full professional engine for match prediction, tournament simulation, and value‑bet analysis.

---

# 🧠 1. Hybrid Prediction Model (Poisson + ML + Odds)

The new prediction model combines three sources of information:

### 1.1 Statistical Poisson Model
- predicts expected goals using exponential functions  
- inputs: team ratings, xG, home advantage  
- outputs: λ_home, λ_away  

### 1.2 ML‑light Model (Extended Features)
Uses:
- rating_diff  
- xg_diff  
- form_diff (Elo form)  
- injury_diff  
- implied odds (bookmaker probabilities)  

### 1.3 Combined Model
Final probability:
- 65% Poisson/Dixon–Coles  
- 35% implied odds  

---

# 🎯 2. Dixon–Coles Correction

The Dixon–Coles model adjusts Poisson predictions to better model:

- low‑scoring matches (0:0, 1:0, 0:1)  
- correlation between goals  
- penalization of extreme scorelines  

Uses correlation factor ρ ≈ 0.13.

Benefits:
- higher prediction accuracy  
- better modeling of draws  
- improved realism for low‑goal matches  

---

# 🔁 3. Bayesian Updating (Model Learns After Each Match)

After every completed match, the model automatically updates:

- intercepts (team goal‑scoring strength)  
- rating and xG weights  
- adapts to real tournament performance  

Benefits:
- model adapts to reality  
- accuracy improves during the tournament  
- reacts to surprises (e.g., underdog overperforming)  

---

# 📈 4. Elo‑Based Form Model

Each team has its own **Elo rating**, updated after every match.

Usage:
- form = average of last N Elo values  
- form_diff = form_home – form_away  

Benefits:
- dynamic form tracking  
- reacts to performance trends  
- accounts for opponent strength  

---

# 🧩 5. Feature Engineering Module

A unified feature set is created for every match:

- rating_diff  
- xg_diff  
- form_diff  
- injury_diff  
- home_advantage  
- implied odds (home/draw/away)  

Benefits:
- unified data from multiple sources  
- robust input for the hybrid model  

---

# 🧮 6. Model Calibration (Maximum Likelihood)

A new module calibrates model parameters using historical data:

- intercept_home  
- intercept_away  
- beta_rating  
- beta_xg  
- beta_home_adv  

Uses:
- Maximum Likelihood Estimation  
- L‑BFGS‑B optimization  

Benefits:
- model fits real data more accurately  
- can use past World Cups, qualifiers, friendlies  

---

# 🏆 7. Monte‑Carlo Simulation of the Entire Tournament

The simulator can:

- simulate all group matches  
- generate group tables  
- determine qualifiers  
- simulate knockout rounds  
- determine tournament winner  

Simulations: 10,000 – 100,000 runs.

Outputs:
- probability of winning the tournament  
- probability of reaching KO rounds  
- probability of reaching final / semifinal  

---

# 📊 8. Group Qualification Probabilities

For each group:

- simulate the group N times  
- compute qualification probabilities  
- compute probability of finishing 1st  

Example output:
```json
{
  "Argentina": 0.92,
  "Japan": 0.63,
  "Nigeria": 0.41,
  "Canada": 0.04
}

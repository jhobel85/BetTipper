# REAL_DATA_SETUP.md  
Preparing the Application for Real MS 2026 Data

This document describes how to prepare the backend so it can load real FIFA World Cup 2026 data (teams, groups, fixtures) as soon as they are officially published.

## 1. Data Files
Create:
backend/data/teams_ms2026.json
backend/data/matches_ms2026.json


## 2. Import Module
`backend/app/data_loader.py`  
Contains:

- load_teams_from_json  
- load_matches_from_json  
- recompute_predictions  

## 3. Admin Endpoints
`backend/app/routers/admin.py`  
- /admin/load-teams  
- /admin/load-matches  
- /admin/recompute-predictions  

## 4. After FIFA Releases Official Data
1. Fill JSON files  
2. Call admin endpoints  
3. Predictions update automatically  

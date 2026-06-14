from .model import ModelParams

DEFAULT_PARAMS = ModelParams(
    intercept_home=0.1,     # základní gólovost domácích
    intercept_away=-0.1,    # základní gólovost hostů
    beta_rating=0.25,       # vliv rozdílu ratingu
    beta_xg=0.35,           # vliv rozdílu xG
    beta_home_adv=0.20      # domácí výhoda
)

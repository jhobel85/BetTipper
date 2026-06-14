from .model import ModelParams

DEFAULT_PARAMS = ModelParams(
    intercept_home=-0.10,   # balanced expected goals
    intercept_away=-0.10,   # balanced expected goals
    beta_rating=0.32,       # stronger team-strength separation
    beta_xg=0.25,           # moderate xG contribution
    beta_home_adv=0.06      # reduced home bias
)

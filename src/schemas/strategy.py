from pydantic import BaseModel

from src.consts.strategy import StrategyMode


class StrategyParams(BaseModel):
    target_acos: float = 0.80
    mode: StrategyMode = StrategyMode.PROFITABILITY

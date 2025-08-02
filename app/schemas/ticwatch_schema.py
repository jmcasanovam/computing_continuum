from pydantic import BaseModel, root_validator
from datetime import datetime
from typing import Union


class TicWatchData(BaseModel):
    session_id: str
    timestamp: datetime
    tic_accx: float
    tic_accy: float
    tic_accz: float
    tic_acclx: float
    tic_accly: float
    tic_acclz: float
    tic_girx: float
    tic_giry: float
    tic_girz: float
    tic_hrppg: float
    tic_step: int
    ticwatchconnected: bool = True
    estado_real: Union[str, None] = None
    predicted_state: Union[str, None] = None

class TicWatchDataOrigin(BaseModel):
    session_id: str
    user_id: str
    timestamp: datetime = None
    timeStamp: Union[datetime, None] = None 
    tic_accx: float
    tic_accy: float
    tic_accz: float
    tic_acclx: float
    tic_accly: float
    tic_acclz: float
    tic_girx: float
    tic_giry: float
    tic_girz: float
    tic_hrppg: float
    tic_step: int
    ticwatchconnected: bool

    @root_validator(pre=True)
    def unify_timestamp(cls, values):
        if "timestamp" not in values and "timeStamp" in values:
            values["timestamp"] = values["timeStamp"]
        return values
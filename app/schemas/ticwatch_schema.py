from pydantic import BaseModel
from datetime import datetime

class TicWatchData(BaseModel):
    session_id: str
    timeStamp: datetime
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
    estado_real: str | None = None
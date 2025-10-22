from pydantic import BaseModel
from typing import List

class EventCreate(BaseModel):
    site_id: str
    events: List[dict]

from pydantic import BaseModel


class Identity(BaseModel):
    id: str
    name: str
    createdAt: str
    sampleCount: int = 0

from pydantic import BaseModel

class InstagramMessage(BaseModel):
    object: str
    entry: list

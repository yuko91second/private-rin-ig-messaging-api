from pydantic import BaseModel

class WebhookEvent(BaseModel):
    object: str
    entry: list

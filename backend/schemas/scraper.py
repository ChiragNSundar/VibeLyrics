from pydantic import BaseModel, Field

class ScrapeRequest(BaseModel):
    artist: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)

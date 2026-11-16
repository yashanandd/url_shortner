from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class URLCreate(BaseModel):
    original_url: str = Field(..., description="Target destination URL")
    custom_alias: Optional[str] = Field(None, description="Optional custom short code alias")
    expires_at: Optional[datetime] = Field(None, description="Optional link expiration datetime (UTC)")


class URLUpdate(BaseModel):
    original_url: Optional[str] = Field(None, description="Updated target destination URL")
    status: Optional[str] = Field(None, description="Link status (ACTIVE, DISABLED, EXPIRED)")
    expires_at: Optional[datetime] = Field(None, description="Updated expiration datetime (UTC)")


class URLResponse(BaseModel):
    id: UUID
    short_code: str
    short_url: str
    original_url: str
    custom_alias: Optional[str] = None
    status: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    total_clicks: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

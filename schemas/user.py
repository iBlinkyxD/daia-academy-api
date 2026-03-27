from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class UserCreate(BaseModel):
    daia_user_id: UUID
    first_name: str | None = None
    last_name: str | None = None
    profile_picture_url: str | None = None

class UserRead(BaseModel):
    id: UUID
    daia_user_id: UUID
    total_xp: int
    created_at: datetime
    model_config = {"from_attributes": True}

class UserInterestRead(BaseModel):
    id: UUID
    interest: str
    model_config = {"from_attributes": True}

class UserInterestCreate(BaseModel):
    interest: str

class UserProfileSync(BaseModel):
    daia_user_id: UUID
    first_name: str | None = None
    last_name: str | None = None
    profile_picture_url: str | None = None

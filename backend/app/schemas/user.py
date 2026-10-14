from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.user import Role


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime


class UserAdminOut(UserOut):
    document_count: int = 0


class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str


class UserStatusUpdate(BaseModel):
    is_active: bool

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    # NOTE: there is intentionally no "role" field. Self-registration always creates a `user`.


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

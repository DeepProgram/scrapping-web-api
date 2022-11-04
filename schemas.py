from pydantic import BaseModel


class SignupInfo(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str


class LoginInfo(BaseModel):
    email: str
    password: str

from passlib.context import CryptContext

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str):
    return bcrypt_context.hash(password)


def verify_password(password: str, hashed_password: str):
    return bcrypt_context.verify(password, hashed_password)

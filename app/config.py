from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./storage.db"
    STORAGE_PATH: str = "./storage"
    SECRET_KEY: str = "your-secret-key-for-jwt"
    
    class Config:
        env_file = ".env"

settings = Settings() 
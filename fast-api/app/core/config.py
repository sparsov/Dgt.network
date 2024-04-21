from pydantic_settings import BaseSettings
from environs import Env
env = Env()
env.read_env()

class Settings(BaseSettings):
    PROJECT_NAME: str = "DGT API Project"
    API_PREFIX: str = env.str("API_PREFIX", default="/api/v1")
    PROJECT_DOCS: str = env.str("PROJECT_DOCS", default="/api/docs")
    CRYPTO_BACK: str = env.str("CRYPTO_BACK", default="openssl")
    API: int = env.int("API", default=8003)
    VERSION: str = env.str("VERSION", default="0.0.1")
    DGT_CONNECT : str = env.str("DGT_CONNECT",default="tcp://validator-dgt-c1-1:4104")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()



from pydantic_settings import BaseSettings
from environs import Env
env = Env()
env.read_env()

class Settings(BaseSettings):
    VERSION: str = env.str("VERSION", default="0.0.2")
    PROJECT_NAME: str = "DGT API Project"
    API_PREFIX: str = env.str("API_PREFIX", default="/api/v1")
    PROJECT_DOCS: str = env.str("PROJECT_DOCS", default="/api/docs")
    CRYPTO_BACK: str = env.str("CRYPTO_BACK", default="openssl")
    API: int = env.int("API", default=8003)
    VERSION: str = env.str("VERSION", default="0.0.1")
    DGT_CONNECT : str = env.str("DGT_CONNECT",default="tcp://validator-dgt-c1-1:4104")
    TOKEN_DB_FILENAME : str = env.str("TOKEN_DB_FILENAME",default="/project/peer/data/tokens.lmdb")
    DEFAULT_DB_SIZE: int = env.int("DEFAULT_DB_SIZE", default=1024*1024*1)
    OPENTSDB_ENABLE: int = env.int("OPENTSDB_ENABLE",default=1)
    OPENTSDB_URL: str = env.str("OPENTSDB_URL",default="http://stats-influxdb-dgt:8086")
    OPENTSDB_DB: str = env.str("OPENTSDB_DB",default="metrics")  
    OPENTSDB_UNAME: str = env.str("OPENTSDB_UNAME",default="lrdata")
    OPENTSDB_PASSW: str = env.str("OPENTSDB_PASSWD",default="pwlrdata") 
    REPORTING_INTERVAL: int =  env.int("REPORTING_INTERVAL",default=10)
    REPORTING_PREFIX: str = env.str("REPORTING_PREFIX",default="dgt_rest_api")
    DEFAULT_TIMEOUT: int =  env.int("DEFAULT_TIMEOUT",default=300)
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()



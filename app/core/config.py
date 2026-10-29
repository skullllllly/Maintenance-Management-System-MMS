from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

  #potegraSQL database configruation 
  POSTGRES_USER: str
  POSTGRES_PASSWORD: str
  POSTGRES_SERVER: str="localhost"
  POSTGRES_PORT:int =5432
  POSTGRES_DB:str

  #minio configruation 

  MINIO_ENDPOINT:str ="localhost:9000"
  MINIO_ACCESS_KEY:str
  MINIO_SECRET_KEY:str
  MINIO_BUCKET_NAME: str="tickets-images"
  MINIO_SECURE:bool =False

  #sitting for security layer
  JWT_SECRET_KEY:str ="change-me-in-production"
  JWT_ALGORITHM:str="HS256"
  ACCESS_TOKEN_EXPIRE_MINUTES:int=60

  model_config=SettingsConfigDict  (

    env_file=".env",
    env_file_encoding="utf-8",
    case_sensitive=True,
    extra="ignore"
  )

  @property
  def async_database_url(self) ->str:
    return (
        f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
        f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    )



settings=Settings()


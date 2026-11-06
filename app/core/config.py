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

  IMAGE_MAX_BYTES:int =15 * 1024 * 1024 
  IMAGE_BLUR_THRESHOLD: float =100.0
  CNN_MODEL_PATH:str = "/models/resnet50_ticket_image.pt"
  CNN_MODEL_DEVICE:str= "cpu"

  XGBOOST_MODEL_PATH: str = "models/xgboost_defect_classifier.joblib"
  XGBOOST_MODEL_VERSION: str = "xgboost-defect-v1"
  CLASSIFIER_LABELS: str =""

  ML_MIN_PROBABILITY: float =0.0
  ML_FEATURE_DIMENSION: int= 2048

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


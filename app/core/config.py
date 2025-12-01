from pydantic_settings import BaseSettings # <-- CORRECT IMPORT
from pydantic import Field # <-- CORRECT IMPORT
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class Settings(BaseSettings):
    # Database Settings
    DATABASE_URL: str = Field(..., description="MySQL database connection string.")

    # Security Settings (JWT)
    SECRET_KEY: str = Field(..., description="Secret key for JWT generation.")
    ALGORITHM: str = Field("HS256", description="Algorithm used for JWT encryption.")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, description="Lifetime of the access token in minutes.")

    # LLM Settings
    HUGGINGFACE_API_KEY: str = Field(..., description="API key for Hugging Face Inference service.")

# Instantiate settings object
settings = Settings()
# ... (Imports remain the same) ...

class Settings(BaseSettings):
    # Database Settings
    DATABASE_URL: str = Field(..., description="MySQL database connection string.")

    # Security Settings (JWT)
    SECRET_KEY: str = Field(..., description="Secret key for JWT generation.")
    ALGORITHM: str = Field("HS256", description="Algorithm used for JWT encryption.")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, description="Lifetime of the access token in minutes.")

    # LLM Settings (Updated for Hugging Face)
    # Changed OPENAI_API_KEY to HUGGINGFACE_API_KEY
    HUGGINGFACE_API_KEY: str = Field(..., description="API key for Hugging Face Inference service.") 

# Instantiate settings object
settings = Settings()
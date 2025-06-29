import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings"""
    
    # Supabase
    SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY: str = os.environ.get("SUPABASE_SERVICE_KEY", "")
    SUPABASE_ANON_KEY: str = os.environ.get("SUPABASE_ANON_KEY", "")
    SUPABASE_JWT_SECRET: str = os.environ.get("SUPABASE_JWT_SECRET", "")
    
    # OpenAI
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    
    # API Settings
    API_HOST: str = os.environ.get("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.environ.get("API_PORT", "8000"))
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
    
    # News Source
    YAHOO_FINANCE_URL: str = "https://finance.yahoo.com/topic/latest-news/"
    
    # Scraper Settings
    SCRAPER_TIMEOUT: int = int(os.environ.get("SCRAPER_TIMEOUT", "40"))
    MAX_RETRIES: int = int(os.environ.get("MAX_RETRIES", "3"))
    
    def validate(self):
        """Validate required environment variables"""
        missing = []
        if not self.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not self.SUPABASE_SERVICE_KEY:
            missing.append("SUPABASE_SERVICE_KEY")
        if not self.SUPABASE_JWT_SECRET:
            missing.append("SUPABASE_JWT_SECRET")
        if not self.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

settings = Settings() 
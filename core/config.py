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
    
    # Email/SMTP 配置
    SMTP_SERVER: str = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER: str = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD: str = os.environ.get("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.environ.get("FROM_EMAIL", "noreply@finnews-bot.com")
    
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
            
    def validate_email_config(self):
        """Validate email configuration (optional)"""
        email_missing = []
        if not self.SMTP_USER:
            email_missing.append("SMTP_USER")
        if not self.SMTP_PASSWORD:
            email_missing.append("SMTP_PASSWORD")
        
        if email_missing:
            print(f"WARNING: Email delivery disabled - missing: {', '.join(email_missing)}")
            return False
        return True

settings = Settings() 
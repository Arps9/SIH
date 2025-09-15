from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ✅ Replace with your actual MySQL username + password
USER = "kmrl_user"        # or "root" if you prefer root
PASSWORD = "password123"  # update if you changed it
HOST = "localhost"
DB_NAME = "kmrl_docs"

# ✅ MySQL connection string
DATABASE_URL = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}/{DB_NAME}"

# Create engine & session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

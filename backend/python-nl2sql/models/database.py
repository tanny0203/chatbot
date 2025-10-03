import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Main database URL (for metadata: users, chats, files, messages)
MAIN_DATABASE_URL = os.getenv(
    "MAIN_DATABASE_URL", 
    "postgresql://balaji:balaji2005@localhost:5432/tempdb?sslmode=disable"
)

# File storage database URL (for actual file data storage)
FILE_STORAGE_DATABASE_URL = os.getenv(
    "FILE_STORAGE_DATABASE_URL", 
    "postgresql://balaji:balaji2005@localhost:5432/filestorage?sslmode=disable"  # Separate database for file data
)

# Main database engine and session
main_engine = create_engine(MAIN_DATABASE_URL)
MainSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=main_engine)

# File storage database engine and session
file_storage_engine = create_engine(FILE_STORAGE_DATABASE_URL)
FileStorageSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=file_storage_engine)

Base = declarative_base()

def get_main_db():
    """Get main database session for metadata (users, chats, files, messages)"""
    db = MainSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_file_storage_db():
    """Get file storage database session for actual file data"""
    db = FileStorageSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Backward compatibility
def get_db():
    """Backward compatibility - returns main database session"""
    return get_main_db()
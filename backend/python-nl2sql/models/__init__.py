# Import all models to ensure they're registered with SQLAlchemy
from .user import User
from .chat import Chat
from .file import File
from .column_metadata import ColumnMetadata

__all__ = ['User', 'Chat', 'File', 'ColumnMetadata']
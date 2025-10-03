from uuid import UUID
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class File(Base):
    __tablename__ = "files"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    chat_id = Column(PostgresUUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    table_name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # These relationships are just for reference - actual data handling will be in Go
    # user = relationship("User", back_populates="files")
    # chat = relationship("Chat", back_populates="files")
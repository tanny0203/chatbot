from uuid import UUID
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class Chat(Base):
    __tablename__ = "chats"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
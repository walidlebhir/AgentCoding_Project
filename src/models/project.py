import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.Config.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(50), nullable=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=True)
    steps: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string of steps
    folder_name: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    download_url: Mapped[str] = mapped_column(String(500), nullable=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=True)  # LLM provider (gemini, groq, crewai)
    model: Mapped[str] = mapped_column(String(100), nullable=True)  # Model name used
    generation_time: Mapped[float] = mapped_column(nullable=True)  # Generation duration in seconds
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    user = relationship("User", back_populates="projects")
    chats = relationship("Chat", back_populates="project", cascade="all, delete-orphan")

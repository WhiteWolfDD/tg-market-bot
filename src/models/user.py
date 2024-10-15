from sqlalchemy import BigInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base
from datetime import datetime
from src.utils.enums import UserRole

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    telegram_user_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True
    )
    username: Mapped[str] = mapped_column(
        String(32),
        nullable=True
    )
    role: Mapped[UserRole] = mapped_column(
        String(20),
        nullable=False,
        default=UserRole.USER.value
    )
    language: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        default="en"
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now()
    )

    # Relationships
    advertisements = relationship(
        "Advertisement",
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    user_advertisement_links = relationship(
        "UserAdvertisement",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            'telegram_user_id': self.telegram_user_id,
            'language': self.language,
            'username': self.username
        }
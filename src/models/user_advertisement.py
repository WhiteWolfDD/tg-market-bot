from sqlalchemy import ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base
from datetime import datetime


class UserAdvertisement(Base):
    __tablename__ = "user_advertisement"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'),
        nullable=False
    )
    advertisement_id: Mapped[int] = mapped_column(
        ForeignKey('advertisements.id'),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="user_advertisement_links")
    advertisement = relationship("Advertisement", back_populates="user_advertisement_links")
from datetime import datetime

from sqlalchemy import ForeignKey, func, CheckConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.database import Base


class AdvertisementRequest(Base):
    """
    SQL model for advertisement requests.
    Represents a user's request to create an advertisement.
    """

    __tablename__ = "advertisement_requests"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'),
        nullable=False
    )
    owner = relationship("User", back_populates="advertisement_requests")

    advertisement_id: Mapped[int] = mapped_column(
        ForeignKey('advertisements.id'),
        nullable=False
    )
    advertisement = relationship("Advertisement", back_populates="requests")

    created_at: Mapped[datetime] = mapped_column(
        func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint("price >= 0", name="check_price_positive"),
    )

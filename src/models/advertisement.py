from datetime import datetime
from decimal import Decimal

from sqlalchemy import Numeric, String, ARRAY, ForeignKey, func, CheckConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.database import Base
from src.utils.enums import AdvertisementStatus


class Advertisement(Base):
    """
    SQL model for advertisements.
    Represents a user's advertisement in the system.
    """

    __tablename__ = "advertisements"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'),
        nullable=False
    )
    owner = relationship("User", back_populates="advertisements")

    category_id: Mapped[int] = mapped_column(
        ForeignKey('categories.id'),
        nullable=False
    )
    category = relationship('Category', back_populates='advertisements')

    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    description: Mapped[str] = mapped_column(
        String(1000),
        nullable=False
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    location: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    status: Mapped[AdvertisementStatus] = mapped_column(
        String(10),
        nullable=False,
        default=AdvertisementStatus.PENDING.value,
        index=True
    )
    files: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=True
    )
    hashtags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    deleted_at: Mapped[datetime] = mapped_column(
        nullable=True,
        index=True
    )

    # Relationships
    user_advertisement_links = relationship(
        "UserAdvertisement",
        back_populates="advertisement",
        cascade="save-update, merge, delete"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint('price >= 0', name='check_price_positive'),
    )
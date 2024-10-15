from datetime import datetime
from decimal import Decimal
from enum import Enum

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

    # Logic
    @property
    def is_active(self) -> bool:
        return self.status == AdvertisementStatus.APPROVED and self.deleted_at is None

    @property
    def is_pending(self) -> bool:
        return self.status == AdvertisementStatus.PENDING and self.deleted_at is None

    @property
    def is_rejected(self) -> bool:
        return self.status == AdvertisementStatus.REJECTED and self.deleted_at is None

    def validate(self):
        if not self.title or len(self.title) > 100:
            raise ValueError("Title is required and must be less than 100 characters.")
        if not self.description or len(self.description) > 1000:
            raise ValueError("Description is required and must be less than 1000 characters.")
        if self.price < 0:
            raise ValueError("Price cannot be negative.")
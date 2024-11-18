from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Numeric, String, ARRAY, ForeignKey, func, CheckConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.database import Base
from src.utils.const import AdvertisementStatus


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
    reason: Mapped[str] = mapped_column(
        String(1000),
        nullable=False
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    location: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    contact_info: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    status: Mapped[AdvertisementStatus] = mapped_column(
        String(10),
        nullable=False,
        default=AdvertisementStatus.PENDING,
        index=True
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

    # Relationships
    user_advertisement_links = relationship(
        "UserAdvertisement",
        back_populates="advertisement",
        cascade="save-update, merge, delete"
    )

    media_files = relationship(
        "MediaFile",
        back_populates="advertisement",
        cascade="save-update, merge, delete"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint('price >= 0', name='check_price_positive'),
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'category_id': self.category_id,
            'title': self.title,
            'description': self.description,
            'reason': self.reason,
            'price': str(self.price),
            'location': self.location,
            'contact_info': self.contact_info,
            'status': self.status,
            'hashtags': self.hashtags,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
from datetime import datetime

from sqlalchemy import func, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base

class Statistic(Base):
    __tablename__ = "statistics"

    __table_args__ = (
        Index('idx_statistics_id', 'id'),
        Index('idx_statistics_updated_at', 'updated_at'),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=False  # We only have one row in this table
    )
    total_users: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )
    new_users_today: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )
    active_users: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )
    total_advertisements: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )
    active_advertisements: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )
    successful_advertisements: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )
    deleted_advertisements: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )
    total_categories: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )
    popular_categories: Mapped[dict] = mapped_column(
        JSONB,
        nullable=True
    )
    response_time_avg: Mapped[float] = mapped_column(
        nullable=False,
        default=0.0
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

    def to_dict(self):
        return {
            'id': self.id,
            'total_users': self.total_users,
            'new_users_today': self.new_users_today,
            'active_users': self.active_users,
            'total_advertisements': self.total_advertisements,
            'active_advertisements': self.active_advertisements,
            'successful_advertisements': self.successful_advertisements,
            'deleted_advertisements': self.deleted_advertisements,
            'total_categories': self.total_categories,
            'popular_categories': self.popular_categories,
            'response_time_avg': self.response_time_avg,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
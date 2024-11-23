from datetime import datetime

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class MediaFile(Base):
    __tablename__ = "media_files"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    advertisement_id: Mapped[int] = mapped_column(
        ForeignKey('advertisements.id'),
        nullable=False
    )
    file_id: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    media_type: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    expiration_date: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("NOW() + INTERVAL '30 days'")
    )

    advertisement = relationship("Advertisement", back_populates="media_files")

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'advertisement_id': self.advertisement_id,
            'file_id': self.file_id,
            'media_type': self.media_type
        }

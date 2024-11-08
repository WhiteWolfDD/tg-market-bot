from sqlalchemy import Integer, String, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.database import Base

class Category(Base):
    __tablename__ = 'categories'
    __table_args__ = (
        Index('idx_categories_id', 'id'),
        Index('idx_categories_parent_id', 'parent_id'),
        Index('idx_categories_path', 'path'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    emoji: Mapped[str] = mapped_column(String(10), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('categories.id'), nullable=True)
    status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    path: Mapped[str] = mapped_column(String, nullable=False, default='')

    parent = relationship('Category', remote_side=[id], backref='children')
    translations = relationship('CategoryTranslation', back_populates='category', cascade='all, delete-orphan')
    advertisements = relationship('Advertisement', back_populates='category')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'emoji': self.emoji,
            'parent_id': self.parent_id,
            'status': self.status,
            'path': self.path,
            'translations': [translation.to_dict() for translation in self.translations] if self.translations else []
        }

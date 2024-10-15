from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.database import Base

class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    emoji: Mapped[str] = mapped_column(String(10), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('categories.id'), nullable=True)

    # Отношения
    parent = relationship('Category', remote_side=[id], backref='children')
    translations = relationship('CategoryTranslation', back_populates='category', cascade='all, delete-orphan')
    advertisements = relationship('Advertisement', back_populates='category')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'emoji': self.emoji,
            'parent_id': self.parent_id,
            'translations': [translation.to_dict() for translation in self.translations] if self.translations else []
        }
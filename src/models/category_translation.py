from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.database import Base

class CategoryTranslation(Base):
    __tablename__ = 'category_translations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('categories.id'), nullable=False)
    language_code: Mapped[str] = mapped_column(String(2), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    category = relationship('Category', back_populates='translations')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'category_id': self.category_id,
            'language_code': self.language_code,
            'name': self.name
        }
from app.backend.db import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from datetime import datetime
from sqlalchemy.orm import relationship

class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    rating_id = Column(Integer, ForeignKey('ratings.id'), nullable=False)
    comment = Column(String)
    comment_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    products = relationship('Product', back_populates='reviews')
    user = relationship('User', back_populates='reviews')
    ratings = relationship('Rating', back_populates='reviews')
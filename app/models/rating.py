from app.backend.db import Base
from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

class Rating(Base):
    __tablename__ = 'ratings'

    id = Column(Integer, primary_key=True, index=True)
    grade = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    is_active = Column(Boolean, default=True)

    user = relationship('User', back_populates='ratings')
    reviews = relationship('Review', back_populates='ratings')
    products = relationship('Product', back_populates='ratings')

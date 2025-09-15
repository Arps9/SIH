from sqlalchemy import Column, Integer, String, Text
from database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255))
    text = Column(Text)
    summary = Column(Text, nullable=True)
    entities = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)   # 👈 NEW FIELD

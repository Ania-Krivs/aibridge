from data.db import Base
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True)
    openai_key = Column(String, nullable=False)
    # tokens = Column(Integer, default=0)
    
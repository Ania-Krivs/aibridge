from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL


metadata = MetaData()

engine = create_engine(DATABASE_URL)
sessions = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

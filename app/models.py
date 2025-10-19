from datetime import datetime
from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql.expression import text
from .shared.database import Base



class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String(200), nullable=False)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))



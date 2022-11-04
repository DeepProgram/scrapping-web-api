from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer
from db.db_sql import Base


class Upwork(Base):
    __tablename__ = "upwork_info"
    index = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=False)
    search_query = Column(String)
    search_result = Column(JSON)
    add_time = Column(Integer)

    def __int__(self, user_id, search_query, search_result, add_time):
        self.user_id = user_id
        self.search_query = search_query
        self.search_result = search_result
        self.add_time = add_time


class User(Base):
    __tablename__ = "user_info"
    user_id = Column(String, primary_key=True)
    email = Column(String)
    password = Column(String)
    first_name = Column(String)
    last_name = Column(String)

    def __int__(self, user_id, email, password, first_name, last_name):
        self.user_id = user_id
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name


class ScrapingStatus(Base):
    __tablename__ = "scraping_status"
    index = Column(Integer, primary_key=True, index=True)
    user_id = Column(String)
    status = Column(String)

    def __int__(self, user_id, status):
        self.user_id = user_id
        self.status = status

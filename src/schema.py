from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, create_engine, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker, joinedload

engine = create_engine('sqlite:///message_db.sqlite3', echo=False)

Base = declarative_base()

class Member(Base):
    __tablename__ = 'members'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    mention_string = Column(String)
    is_bot = Column(Boolean)

    def __str__(self):
       return f"{self.name}"

class Channel(Base):
    __tablename__ = 'channels'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __str__(self):
       return f"{self.name}"

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    text = Column(String)
    date_sent = Column(DateTime)

    channel_id = Column(Integer, ForeignKey('channels.id'))
    channel = relationship("Channel", backref=backref('messages', lazy='dynamic'))    
    member_id = Column(Integer, ForeignKey('members.id'))
    member = relationship("Member", backref=backref('messages', lazy='dynamic'))

    def __str__(self):
       return f"{self.id}"


Base.metadata.create_all(engine) 

Session = sessionmaker(bind=engine)

def GetSession():
    return Session()
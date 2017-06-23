from sqlalchemy import Column, Date, Float, Integer, String, Text, text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class OAuthData(Base):
    __tablename__ = 'oauthdata'

    param = Column(String(50), primary_key=True, unique=True)
    value = Column(String(255))

    def __repr__(self):
        return "Key: {} Value: {} ".format(self.param, self.value)


class TimeSheet(Base):
    __tablename__ = 'timesheets'

    key = Column(Integer, primary_key=True)
    userid = Column(Integer, nullable=False)
    time_spent = Column(Float, nullable=False)
    description = Column(Text)
    activity_date = Column(Date, nullable=False, index=True)
    id = Column(String(60), nullable=False, unique=True)
    created_by = Column(String(60))
    name = Column(String(512))
    source = Column(String(10), index=True)

    def __repr__(self):
        return "Key: {}, UserId: {}, Time_Spent: {}, Description: {}, " \
               "Activity_Date: {}, Id: {}, Created_By: {}, Name: {}, Source: {}".format(self.key, self.time_spent,
                                                                                        self.description,
                                                                                        self.activity_date, self.id,
                                                                                        self.created_by, self.name,
                                                                                        self.source)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    sugar_id = Column(String(40))
    sugar_uname = Column(String(45), nullable=False, unique=True)
    intetics_uname = Column(String(45), unique=True)
    location = Column(String(1), server_default=text("'M'"))
    dissmissed = Column(String(1), server_default=text("'N'"))
    team = Column(String(45))
    full_name = Column(String(100))

    def __repr__(self):
        return "Id: {}, Sugar_Id: {}, Sugar_Uname: {}, Intetics_Uname: {}," \
               "Location: {}, Dissmissed: {}, Team: {}, Full_Name: {}".format(self.id, self.sugar_id, self.sugar_uname,
                                                                              self.intetics_uname, self.location,
                                                                              self.dissmissed, self.team,
                                                                              self.full_name)

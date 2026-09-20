from sqlalchemy import Column, Integer, String, Time, DateTime, Text, Boolean, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


class Timetable(Base):
    __tablename__ = "timetable"

    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, nullable=False)
    day = Column(String, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    class_type = Column(String, nullable=False)


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    day = Column(String, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    estimated_minutes = Column(Integer, nullable=False)
    deadline = Column(DateTime, nullable=False)
    priority = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    is_fixed = Column(Boolean, nullable=False)
    fixed_start_time = Column(Time)
    fixed_end_time = Column(Time)


class Schedule(Base):
    __tablename__ = "schedule"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(String, nullable=False)
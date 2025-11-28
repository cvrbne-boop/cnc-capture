from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, JSON, UniqueConstraint
from sqlalchemy.sql import func
import enum
from app.db.base import Base
from sqlalchemy.orm import relationship

class SessionStatus(str, enum.Enum):
    started = "started"
    stopped = "stopped"
    cancelled = "cancelled"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    full_name = Column(String)
    email = Column(String)

class Machine(Base):
    __tablename__ = "machines"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    customer = Column(String)

class Drawing(Base):
    __tablename__ = "drawings"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    drawing_number = Column(String)
    planned_time_per_piece = Column(Integer, default=0)
    planned_pieces = Column(Integer, default=1)

    job = relationship("Job")

class JobCard(Base):
    __tablename__ = "job_cards"
    id = Column(Integer, primary_key=True)
    drawing_id = Column(Integer, ForeignKey("drawings.id"))
    card_number = Column(String)
    qr_payload = Column(String)

    drawing = relationship("Drawing")

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    job_card_id = Column(Integer, ForeignKey("job_cards.id"))
    operator_id = Column(Integer, ForeignKey("users.id"))
    machine_id = Column(Integer, ForeignKey("machines.id"))
    piece_index = Column(Integer, default=1)
    start_ts = Column(DateTime(timezone=True), server_default=func.now())
    stop_ts = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    status = Column(Enum(SessionStatus), default=SessionStatus.started)
    meta = Column(JSON, nullable=True)

    job_card = relationship("JobCard")
    operator = relationship("User")
    machine = relationship("Machine")

    __table_args__ = (
        UniqueConstraint('job_card_id', 'piece_index', 'machine_id', 'operator_id', name='uniq_piece_owner'),
    )

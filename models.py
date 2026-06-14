from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    ip_range = Column(String, nullable=False)
    gateway = Column(String, nullable=True)
    ports_scanned = Column(String, nullable=False)
    status = Column(String, nullable=False, default="queued")
    mode = Column(String, nullable=False, default="demo")

    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)

    hosts = relationship(
        "Host",
        back_populates="scan",
        cascade="all, delete-orphan"
    )


class Host(Base):
    __tablename__ = "hosts"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    ip_address = Column(String, nullable=False)
    mac_address = Column(String, nullable=False)

    scan = relationship("Scan", back_populates="hosts")
    open_ports = relationship(
        "OpenPort",
        back_populates="host",
        cascade="all, delete-orphan"
    )


class OpenPort(Base):
    __tablename__ = "open_ports"

    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(Integer, ForeignKey("hosts.id"), nullable=False)
    port = Column(Integer, nullable=False)

    # 🔗 RELATIONSHIP
    host = relationship("Host", back_populates="open_ports")

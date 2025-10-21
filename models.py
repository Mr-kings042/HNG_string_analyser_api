from datetime import datetime, timezone
from sqlalchemy import JSON, Column, String,  DateTime
from database import Base

class Strings(Base):
    __tablename__ = "strings"

    id = Column(String, primary_key=True, index=True)
    value = Column(String, index=True, nullable=False)
    properties = Column(JSON, nullable=False)  # Store as JSON string
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
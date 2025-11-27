from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from .database import Base


class UserRole(str, Enum):
    """User roles for access control."""
    ADMIN = "admin"  # Full access
    DESIGNER = "designer"  # Can create/edit jobs
    OPERATOR = "operator"  # Can manage local queue and print
    VIEWER = "viewer"  # Read-only access


class User(Base):
    """
    User accounts for designers and operators.
    Print agents authenticate via API keys on the Printer model instead.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Auth
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(100))
    role = Column(SQLEnum(UserRole), default=UserRole.DESIGNER, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
    
    @property
    def can_design(self) -> bool:
        return self.role in [UserRole.ADMIN, UserRole.DESIGNER]
    
    @property
    def can_operate(self) -> bool:
        return self.role in [UserRole.ADMIN, UserRole.OPERATOR]




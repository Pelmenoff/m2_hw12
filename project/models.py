from sqlalchemy import Column, String, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr
from datetime import date
from database import Base
from typing import List


class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: date
    additional_data: str


class ContactResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: date
    additional_data: str

    class Config:
        orm_mode = True


class ContactListResponse(BaseModel):
    contacts: List[ContactResponse]

    class Config:
        orm_mode = True


class UserResponse(BaseModel):
    id: int
    email: str

    class Config:
        orm_mode = True


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, index=True, unique=True)
    phone_number = Column(String, index=True)
    birthday = Column(Date)
    additional_data = Column(String)

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="contacts")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    contacts = relationship("Contact", back_populates="owner")

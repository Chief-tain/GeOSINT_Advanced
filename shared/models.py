from __future__ import annotations

from datetime import datetime

from sqlalchemy import (BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, MetaData, SmallInteger, String,
                        Table, UniqueConstraint, LargeBinary)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, FLOAT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class"""

    metadata = MetaData(
        naming_convention={
            'ix': 'ix_%(column_0_label)s',
            'uq': 'uq_%(table_name)s_%(column_0_name)s',
            'ck': 'ck_%(table_name)s_`%(constraint_name)s`',
            'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
            'pk': 'pk_%(table_name)s',
        }
    )


class RuTgData(Base):
    __tablename__ = 'ru_tg_data'

    id: Mapped[int] = mapped_column(
        'id',
        Integer,
        primary_key=True,
        autoincrement=True
    )
    message_id: Mapped[str] = mapped_column(
        'message_id',
        Integer,
        nullable=True,
        default=None
    )
    sender: Mapped[str] = mapped_column(
        'sender',
        String,
        nullable=True,
        default=None
    )
    chat_title: Mapped[str] = mapped_column(
        'chat_title',
        String,
        nullable=True,
        default=None
        )
    date: Mapped[str] = mapped_column(
        'date',
        Integer,
        nullable=True,
        default=None
    )
    text: Mapped[str] = mapped_column(
        'text',
        String,
        nullable=True,
        default=None
    )
    tokens: Mapped[list[str]] = mapped_column(
       'tokens',
       ARRAY(String),
       nullable=True,
       default=[]
    )
    embedding: Mapped[list[FLOAT]] = mapped_column(
       'embedding',
       ARRAY(FLOAT),
       nullable=True,
       default=[]
    )
    

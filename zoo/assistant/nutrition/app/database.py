from typing import *
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import JSON, PickleType
from datetime import datetime

Base = declarative_base()


class DiaryRecord(Base):
    __tablename__ = "diary"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column()
    timestamp: Mapped[datetime] = mapped_column()
    food: Mapped[str] = mapped_column()
    amount: Mapped[float] = mapped_column()
    unit: Mapped[str] = mapped_column()



class FoodUnit(Base):
    __tablename__ = 'food_units'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    food: Mapped[str] = mapped_column()
    unit: Mapped[str] = mapped_column()
    weight: Mapped[int] = mapped_column()



class ReferenceIntake(Base):
    __tablename__ = 'reference_intake'

    food: Mapped[str] = mapped_column(primary_key=True)
    calories: Mapped[float] = mapped_column()
    proteins: Mapped[float] = mapped_column()
    fats: Mapped[float] = mapped_column()
    carbs: Mapped[float] = mapped_column()


class WeightMeasurement(Base):
    __tablename__ = 'weight_measurements'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column()
    username: Mapped[str] = mapped_column()
    weight: Mapped[float] = mapped_column()


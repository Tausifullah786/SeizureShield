"""Validation shapes for patient requests and responses."""

from typing import Literal
from pydantic import BaseModel, Field


class PatientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=0, le=120)
    sex: Literal["M", "F", "Other"]
    city: str = Field(min_length=1, max_length=100)


class PatientUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=0, le=120)
    sex: Literal["M", "F", "Other"]
    city: str = Field(min_length=1, max_length=100)


class PatientResponse(BaseModel):
    id: str
    name: str
    age: int
    sex: str
    city: str
    latestStatus: str = "No analysis yet"
    analysesCount: int = 0
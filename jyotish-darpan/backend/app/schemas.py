from datetime import date, time
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class BirthChartRequest(BaseModel):
    name: str = Field(default="", max_length=100)
    birth_date: date
    birth_time: time
    timezone: str = Field(description="IANA timezone, e.g. Asia/Kolkata")
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    ayanamsa: Literal["lahiri"] = "lahiri"
    house_system: Literal["whole_sign"] = "whole_sign"

    @field_validator("timezone")
    @classmethod
    def timezone_must_be_iana(cls, value: str) -> str:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Use a valid IANA timezone such as Asia/Kolkata")
        return value

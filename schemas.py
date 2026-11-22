from datetime import date
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StrictFloat,
    StrictInt,
    StrictStr,
    field_validator,
)
from pydantic_core import PydanticCustomError

import clock


# ============================================================
# CUSTOM VALIDATORS
# ============================================================

def validate_person_name(value: str) -> str:
    value = " ".join(value.split()).strip()

    if len(value) < 2:
        raise ValueError("Give the person's name.")

    return value


def validate_phone(value: str) -> str:
    value = "".join(value.split())

    if len(value) != 10 or not value.isdigit() or not (
        value.startswith("07") or value.startswith("01")
    ):
        raise PydanticCustomError(
            "invalid_phone",
            "Use a mobile number like 0712345678.",
            {"example": "0712345678"},
        )

    return value


def validate_past_day(value: date) -> date:
    if value > clock.today():
        raise ValueError("A day cannot be after today.")

    return value


PersonName = Annotated[StrictStr, AfterValidator(validate_person_name)]
Phone = Annotated[StrictStr, AfterValidator(validate_phone)]
PastDay = Annotated[date, AfterValidator(validate_past_day)]


# ============================================================
# BASE MODELS
# ============================================================

class In(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )


class Out(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )


# ============================================================
# INPUT MODELS
# ============================================================

class ReceiptIn(In):
    farmer: PersonName
    phone: Phone
    crop: StrictStr
    bags: StrictInt = Field(ge=1, le=5000)
    moisture: StrictFloat = Field(gt=0, le=13.5)
    deposited_on: PastDay


class ReceiptPatch(In):
    farmer: PersonName | None = None
    phone: Phone | None = None
    crop: StrictStr | None = None
    bags: StrictInt | None = Field(default=None, ge=1, le=5000)
    moisture: StrictFloat | None = Field(default=None, gt=0, le=13.5)
    deposited_on: PastDay | None = None

    @field_validator("*", mode="before")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Send a value, or leave the field out.")
        return value


class WithdrawalIn(In):
    bags: StrictInt = Field(ge=1)
    taken_on: PastDay
    collected_by: PersonName


# ============================================================
# QUERY MODELS
# ============================================================

class PageQuery(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=False,
    )

    page: int = Field(default=1, ge=1, le=10000)
    per_page: int = Field(default=20, ge=1, le=100)


class ReceiptQuery(PageQuery):
    crop: str | None = None
    status: str | None = None
    sort: str = "id"

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        if value not in {"open", "closed"}:
            raise ValueError("Input should be 'open' or 'closed'")
        return value

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, value):
        allowed = {"id", "bags", "-bags", "deposited_on"}

        if value not in allowed:
            raise ValueError(
                "Input should be 'id', 'bags', '-bags' or 'deposited_on'"
            )

        return value


# ============================================================
# OUTPUT MODELS
# ============================================================

class Receipt(Out):
    id: int
    farmer: str
    phone: str
    crop: str
    bags: int
    bags_left: int
    moisture: float
    deposited_on: date


class ReceiptPage(Out):
    items: list[Receipt]
    page: int
    per_page: int
    total: int


class Withdrawal(Out):
    n: int
    receipt_id: int
    bags: int
    collected_by: str
    taken_on: date
    fee_ksh: int


class WithdrawalList(Out):
    items: list[Withdrawal]


class CropList(Out):
    items: list[str]


class Detail(Out):
    detail: str


class Problem(Out):
    error: str
    details: list[dict] | None = None
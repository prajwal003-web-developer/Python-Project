
from pydantic import BaseModel, Field, ConfigDict


class FacultyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)


class FacultyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    slug: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)


class ProgramCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    faculty: str
    isSemesterWise: bool = True
    total_year: int = Field(ge=1, le=10)


class ProgramUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    faculty: str | None = None
    isSemesterWise: bool | None = None
    total_year: int | None = Field(default=None, ge=1, le=10)


class FacultyWithPrograms(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    programs: list[dict] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)

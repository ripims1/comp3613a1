from typing import Optional

from sqlmodel import Field, SQLModel
from sqlalchemy import UniqueConstraint


class Program(SQLModel, table=True):
    program_id: Optional[int] = Field(default=None, primary_key=True)
    program_name: str
    total_credits_required: int = Field(default=93)


class Course(SQLModel, table=True):
    course_id: Optional[int] = Field(default=None, primary_key=True)
    course_code: str = Field(index=True, unique=True)
    course_title: str
    credits: int


class ProgramCourse(SQLModel, table=True):
    program_course_id: Optional[int] = Field(default=None, primary_key=True)
    program_id: int = Field(foreign_key="program.program_id")
    course_id: int = Field(foreign_key="course.course_id")
    requirement_type: str = "required"


class Student(SQLModel, table=True):
    student_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    program_id: int = Field(foreign_key="program.program_id")
    student_name: str


class CompletedCourse(SQLModel, table=True):
    student_id: int = Field(foreign_key="student.student_id", primary_key=True)
    course_id: int = Field(foreign_key="course.course_id", primary_key=True)
    grade: str
    semester: str
    academic_year: int


class CourseSelection(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("student_id", "semester", "academic_year"),
    )

    selection_id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.student_id")
    semester: str
    academic_year: str = Field(default="2026/2027", index=True)
    status: str = "draft"
    advisor_comment: Optional[str] = None


class SelectedCourse(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("selection_id", "course_id"),
    )

    selected_course_id: Optional[int] = Field(default=None, primary_key=True)
    selection_id: int = Field(foreign_key="courseselection.selection_id")
    course_id: int = Field(foreign_key="course.course_id")

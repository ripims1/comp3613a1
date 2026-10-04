"""Database table models.

Import every table model here so ``SQLModel.metadata.create_all`` sees them.
"""

from app.models.user import User
from app.models.degree import (
    CompletedCourse,
    Course,
    CourseSelection,
    Program,
    ProgramCourse,
    SelectedCourse,
    Student,
)

__all__ = [
    "User",
    "Program",
    "Course",
    "ProgramCourse",
    "Student",
    "CompletedCourse",
    "CourseSelection",
    "SelectedCourse",
]

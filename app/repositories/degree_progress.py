from sqlmodel import Session, select

from app.models.degree import (
    CompletedCourse,
    Course,
    Program,
    ProgramCourse,
    Student,
)


class DegreeProgressRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_student(self, user_id: int) -> Student | None:
        return self.db.exec(
            select(Student).where(Student.user_id == user_id)
        ).one_or_none()

    def get_student_by_id(self, student_id: int) -> Student | None:
        return self.db.exec(
            select(Student).where(Student.student_id == student_id)
        ).one_or_none()

    def get_program(self, program_id: int) -> Program | None:
        return self.db.get(Program, program_id)

    def get_required_courses(self, program_id: int) -> list[tuple[Course, ProgramCourse]]:
        statement = (
            select(Course, ProgramCourse)
            .join(ProgramCourse, ProgramCourse.course_id == Course.course_id)
            .where(ProgramCourse.program_id == program_id)
        )
        return list(self.db.exec(statement).all())

    def get_completed_courses(self, student_id: int) -> list[tuple[CompletedCourse, Course]]:
        statement = (
            select(CompletedCourse, Course)
            .join(Course, Course.course_id == CompletedCourse.course_id)
            .where(CompletedCourse.student_id == student_id)
        )
        return list(self.db.exec(statement).all())

    def set_course_completion(
        self,
        student_id: int,
        course_id: int,
        completed: bool,
    ) -> None:
        record = self.db.exec(
            select(CompletedCourse).where(
                CompletedCourse.student_id == student_id,
                CompletedCourse.course_id == course_id,
            )
        ).one_or_none()
        if completed and record is None:
            self.db.add(
                CompletedCourse(
                    student_id=student_id,
                    course_id=course_id,
                    grade="Completed",
                    semester="",
                    academic_year=0,
                )
            )
        elif not completed and record is not None:
            self.db.delete(record)
        self.db.commit()

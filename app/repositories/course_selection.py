from sqlmodel import Session, select

from app.models.degree import (
    CompletedCourse,
    Course,
    CourseSelection,
    ProgramCourse,
    SelectedCourse,
    Student,
)


class CourseSelectionRepository:
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

    def get_available_courses(self, student_id: int) -> list[Course]:
        completed_course_ids = select(CompletedCourse.course_id).where(
            CompletedCourse.student_id == student_id
        )
        return list(
            self.db.exec(
                select(Course)
                .where(Course.course_id.not_in(completed_course_ids))
                .order_by(Course.course_code)
            ).all()
        )

    def get_selection(
        self,
        student_id: int,
        semester: str,
        academic_year: str,
    ) -> CourseSelection | None:
        return self.db.exec(
            select(CourseSelection).where(
                CourseSelection.student_id == student_id,
                CourseSelection.semester == semester,
                CourseSelection.academic_year == academic_year,
            )
            .order_by(CourseSelection.selection_id.desc())
        ).first()

    def get_selections(self, student_id: int) -> list[CourseSelection]:
        return list(
            self.db.exec(
                select(CourseSelection)
                .where(CourseSelection.student_id == student_id)
                .order_by(
                    CourseSelection.academic_year.desc(),
                    CourseSelection.semester,
                    CourseSelection.selection_id.desc(),
                )
            ).all()
        )

    def get_submitted_selections(self) -> list[CourseSelection]:
        return list(
            self.db.exec(
                select(CourseSelection)
                .where(CourseSelection.status == "submitted")
                .order_by(
                    CourseSelection.academic_year,
                    CourseSelection.semester,
                    CourseSelection.selection_id,
                )
            ).all()
        )

    def get_reviewed_selections(self) -> list[CourseSelection]:
        return list(
            self.db.exec(
                select(CourseSelection)
                .where(
                    CourseSelection.status.in_(
                        ["approved", "rejected"]
                    )
                )
                .order_by(
                    CourseSelection.academic_year.desc(),
                    CourseSelection.semester,
                    CourseSelection.selection_id.desc(),
                )
            ).all()
        )

    def get_selection_by_id(self, selection_id: int) -> CourseSelection | None:
        return self.db.exec(
            select(CourseSelection).where(
                CourseSelection.selection_id == selection_id
            )
        ).one_or_none()

    def update_selection_status(
        self,
        selection_id: int,
        status: str,
        advisor_comment: str | None = None,
    ) -> CourseSelection:
        selection = self.get_selection_by_id(selection_id)
        if selection is None:
            raise ValueError("The semester plan could not be found.")
        if selection.status != "submitted":
            raise ValueError("Only submitted semester plans can be reviewed.")
        selection.status = status
        selection.advisor_comment = advisor_comment
        self.db.add(selection)
        self.db.commit()
        self.db.refresh(selection)
        return selection

    def get_draft(self, student_id: int, semester: str, academic_year: str) -> CourseSelection | None:
        selection = self.get_selection(student_id, semester, academic_year)
        if selection and selection.status == "draft":
            return selection
        return None

    def get_selected_courses(self, selection_id: int) -> list[Course]:
        statement = (
            select(Course)
            .join(SelectedCourse, SelectedCourse.course_id == Course.course_id)
            .where(SelectedCourse.selection_id == selection_id)
            .order_by(Course.course_code)
        )
        return list(self.db.exec(statement).all())

    def get_selected_course_details(
        self,
        selection_id: int,
        student_id: int,
    ) -> list[tuple[Course, ProgramCourse | None]]:
        student = self.get_student_by_id(student_id)
        if student is None:
            return []
        statement = (
            select(Course, ProgramCourse)
            .join(SelectedCourse, SelectedCourse.course_id == Course.course_id)
            .outerjoin(
                ProgramCourse,
                (ProgramCourse.course_id == Course.course_id)
                & (ProgramCourse.program_id == student.program_id),
            )
            .where(SelectedCourse.selection_id == selection_id)
            .order_by(Course.course_code)
        )
        return list(self.db.exec(statement).all())

    def delete_selection(self, student_id: int, selection_id: int) -> None:
        selection = self.db.exec(
            select(CourseSelection).where(
                CourseSelection.selection_id == selection_id,
                CourseSelection.student_id == student_id,
            )
        ).one_or_none()
        if selection is None:
            raise ValueError("The semester plan could not be found.")

        selected_courses = self.db.exec(
            select(SelectedCourse).where(
                SelectedCourse.selection_id == selection_id
            )
        ).all()
        for selected_course in selected_courses:
            self.db.delete(selected_course)
        self.db.flush()
        self.db.delete(selection)
        self.db.commit()

    def save_draft(
        self,
        student_id: int,
        semester: str,
        academic_year: str,
        course_ids: list[int],
    ) -> CourseSelection:
        selection = self.get_draft(student_id, semester, academic_year)
        if selection is None:
            existing = self.get_selection(student_id, semester, academic_year)
            if existing and existing.status == "rejected":
                selection = existing
                selection.status = "draft"
                selection.advisor_comment = None
                self.db.add(selection)
                self.db.flush()
            elif existing is not None:
                raise ValueError(
                    "This semester plan has already been reviewed and cannot be edited."
                )
            else:
                selection = CourseSelection(
                    student_id=student_id,
                    semester=semester,
                    academic_year=academic_year,
                )
                self.db.add(selection)
                self.db.flush()

        existing = self.db.exec(
            select(SelectedCourse).where(
                SelectedCourse.selection_id == selection.selection_id
            )
        ).all()
        for selected in existing:
            self.db.delete(selected)
        self.db.flush()
        for course_id in sorted(set(course_ids)):
            self.db.add(
                SelectedCourse(
                    selection_id=selection.selection_id,
                    course_id=course_id,
                )
            )
        self.db.commit()
        self.db.refresh(selection)
        return selection

    def submit_draft(
        self,
        student_id: int,
        semester: str,
        academic_year: str,
    ) -> CourseSelection:
        selection = self.get_draft(student_id, semester, academic_year)
        if selection is None:
            raise ValueError("Save a draft with at least one course before submitting.")
        selection.status = "submitted"
        self.db.add(selection)
        self.db.commit()
        self.db.refresh(selection)
        return selection

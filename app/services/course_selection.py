from app.repositories.course_selection import CourseSelectionRepository


def _review_summary(repo: CourseSelectionRepository, selection) -> dict:
    student = repo.get_student_by_id(selection.student_id)
    courses = repo.get_selected_courses(selection.selection_id)
    total_credits = sum(course.credits for course in courses)
    return {
        "selection": selection,
        "student": student,
        "courses": courses,
        "course_count": len(courses),
        "total_credits": total_credits,
        "credit_limit_exceeded": total_credits > 15,
    }


def get_advisor_review_data(
    repo: CourseSelectionRepository,
    search: str = "",
) -> list[dict]:
    normalized_search = search.strip().lower()
    reviews = [
        _review_summary(repo, selection)
        for selection in repo.get_submitted_selections()
    ]
    if normalized_search:
        reviews = [
            review
            for review in reviews
            if normalized_search in review["student"].student_name.lower()
            or normalized_search in review["selection"].semester.lower()
            or normalized_search in review["selection"].academic_year.lower()
            or any(
                normalized_search in course.course_code.lower()
                or normalized_search in course.course_title.lower()
                for course in review["courses"]
            )
        ]
    return reviews


def get_advisor_history_data(
    repo: CourseSelectionRepository,
    search: str = "",
) -> list[dict]:
    normalized_search = search.strip().lower()
    history = [
        _review_summary(repo, selection)
        for selection in repo.get_reviewed_selections()
    ]
    if normalized_search:
        history = [
            review
            for review in history
            if normalized_search in review["student"].student_name.lower()
            or normalized_search in review["selection"].semester.lower()
            or normalized_search in review["selection"].academic_year.lower()
            or any(
                normalized_search in course.course_code.lower()
                or normalized_search in course.course_title.lower()
                for course in review["courses"]
            )
        ]
    return history


def get_advisor_selection_data(
    repo: CourseSelectionRepository,
    selection_id: int,
) -> dict | None:
    selection = repo.get_selection_by_id(selection_id)
    if selection is None:
        return None
    return _review_summary(repo, selection)


def decide_course_selection(
    repo: CourseSelectionRepository,
    selection_id: int,
    decision: str,
    advisor_comment: str | None = None,
) -> None:
    if decision not in {"approved", "rejected"}:
        raise ValueError("Choose either approve or reject for a submitted plan.")
    comment = (advisor_comment or "").strip()
    if decision == "rejected" and not comment:
        raise ValueError("A comment is required when rejecting a course plan.")
    repo.update_selection_status(
        selection_id,
        decision,
        comment or None,
    )


def _selection_summary(
    repo: CourseSelectionRepository,
    selection,
) -> dict:
    courses = repo.get_selected_courses(selection.selection_id)
    total_credits = sum(course.credits for course in courses)
    return {
        "selection": selection,
        "courses": courses,
        "course_count": len(courses),
        "total_credits": total_credits,
        "credit_limit_exceeded": total_credits > 15,
    }


def get_course_planning_data(
    repo: CourseSelectionRepository,
    user_id: int,
    semester: str,
    academic_year: str,
) -> dict:
    student = repo.get_student(user_id)
    if student is None:
        return {"student": None, "courses": [], "selected_ids": []}

    selection = repo.get_selection(student.student_id, semester, academic_year)
    selected = repo.get_selected_courses(selection.selection_id) if selection else []
    selected_details = (
        repo.get_selected_course_details(
            selection.selection_id,
            student.student_id,
        )
        if selection
        else []
    )
    return {
        "student": student,
        "courses": repo.get_available_courses(student.student_id),
        "selected_courses": selected,
        "selected_course_details": selected_details,
        "selected_ids": [course.course_id for course in selected],
        "total_credits": sum(course.credits for course in selected),
        "credit_limit_exceeded": sum(course.credits for course in selected) > 15,
        "selection_status": selection.status if selection else "not_started",
        "submission_details": selection,
        "semester": semester,
        "academic_year": academic_year,
    }


def get_course_selection_history(
    repo: CourseSelectionRepository,
    user_id: int,
) -> list[dict]:
    student = repo.get_student(user_id)
    if student is None:
        return []
    return [
        _selection_summary(repo, selection)
        for selection in repo.get_selections(student.student_id)
    ]


def save_course_plan(
    repo: CourseSelectionRepository,
    user_id: int,
    semester: str,
    academic_year: str,
    course_ids: list[int],
) -> None:
    student = repo.get_student(user_id)
    if student is None:
        raise ValueError("Student profile is required before saving a course plan.")
    repo.save_draft(student.student_id, semester, academic_year, course_ids)


def delete_course_plan(
    repo: CourseSelectionRepository,
    user_id: int,
    selection_id: int,
) -> None:
    student = repo.get_student(user_id)
    if student is None:
        raise ValueError("Student profile is required before deleting a course plan.")
    repo.delete_selection(student.student_id, selection_id)


def submit_course_plan(
    repo: CourseSelectionRepository,
    user_id: int,
    semester: str,
    academic_year: str,
) -> None:
    student = repo.get_student(user_id)
    if student is None:
        raise ValueError("Student profile is required before submitting a course plan.")
    repo.submit_draft(student.student_id, semester, academic_year)

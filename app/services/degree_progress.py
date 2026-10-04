from app.repositories.degree_progress import DegreeProgressRepository


def get_degree_progress(repo: DegreeProgressRepository, user_id: int) -> dict:
    student = repo.get_student(user_id)
    return _build_degree_progress(repo, student)


def get_degree_progress_for_student(
    repo: DegreeProgressRepository,
    student_id: int,
) -> dict | None:
    student = repo.get_student_by_id(student_id)
    if student is None:
        return None
    return _build_degree_progress(repo, student)


def _build_degree_progress(repo: DegreeProgressRepository, student) -> dict:
    if student is None:
        return {
            "student": None,
            "program": None,
            "required_courses": [],
            "completed_courses": [],
            "required_credits": 0,
            "completed_credits": 0,
            "progress_percent": 0,
        }
    program = repo.get_program(student.program_id)
    required_courses = repo.get_required_courses(student.program_id)
    completed_courses = repo.get_completed_courses(student.student_id)
    completed_ids = {course.course_id for _, course in completed_courses}
    completed_credits = sum(
        course.credits
        for _, course in completed_courses
        if course.course_id in {item.course_id for item, _ in required_courses}
    )
    required_credits = program.total_credits_required if program else 0

    return {
        "student": student,
        "program": program,
        "required_courses": [
            (course, link, course.course_id in completed_ids)
            for course, link in required_courses
        ],
        "completed_courses": completed_courses,
        "required_credits": required_credits,
        "completed_credits": completed_credits,
        "progress_percent": round(
            min(completed_credits / required_credits * 100, 100)
            if required_credits
            else 0
        ),
    }


def set_course_completion(
    repo: DegreeProgressRepository,
    student_id: int,
    course_id: int,
    completed: bool,
) -> None:
    repo.set_course_completion(student_id, course_id, completed)

from fastapi import APIRouter, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from urllib.parse import urlencode
from app.dependencies.session import SessionDep
from app.dependencies.auth import AuthDep, IsUserLoggedIn, get_current_user, is_admin
from . import router, templates
from app.repositories.degree_progress import DegreeProgressRepository
from app.services.degree_progress import get_degree_progress, set_course_completion
from app.repositories.course_selection import CourseSelectionRepository
from app.utilities.flash import flash
from app.services.course_selection import (
    get_course_planning_data,
    get_course_selection_history,
    delete_course_plan,
    save_course_plan,
    submit_course_plan,
)


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: AuthDep,
    db:SessionDep
):
    progress = get_degree_progress(DegreeProgressRepository(db), user.id)
    return templates.TemplateResponse(
        request=request, 
        name="app.html",
        context={
            "user": user
            ,"progress": progress
        }
    )


@router.post("/app/progress/course", response_class=RedirectResponse)
async def update_course_completion(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    course_id: int = Form(),
    completed: bool = Form(),
):
    repository = DegreeProgressRepository(db)
    student = repository.get_student(user.id)
    if student is None:
        flash(request, "Student profile is required before updating course progress.", "warning")
        return RedirectResponse(
            url=request.url_for("user_home_view"),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    required_course_ids = {
        course.course_id
        for course, _link in repository.get_required_courses(student.program_id)
    }
    if course_id not in required_course_ids:
        flash(request, "That course is not part of your program requirements.", "warning")
        return RedirectResponse(
            url=request.url_for("user_home_view"),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    set_course_completion(repository, student.student_id, course_id, completed)
    flash(request, "Course status updated.", "success")
    return RedirectResponse(
        url=request.url_for("user_home_view"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/app/planning", response_class=HTMLResponse)
async def course_planning_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    semester: str = "Semester 1",
    academic_year: str = "2026/2027",
):
    planning = get_course_planning_data(
        CourseSelectionRepository(db),
        user.id,
        semester,
        academic_year,
    )
    return templates.TemplateResponse(
        request=request,
        name="course-planning.html",
        context={"user": user, "planning": planning},
    )


@router.post("/app/planning", response_class=RedirectResponse)
async def save_course_selection(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    semester: str = Form(),
    academic_year: str = Form(),
    course_ids: list[int] = Form(default=[]),
):
    try:
        save_course_plan(
            CourseSelectionRepository(db),
            user.id,
            semester,
            academic_year,
            course_ids,
        )
    except ValueError as exc:
        flash(request, str(exc), "warning")
    return RedirectResponse(
        url=f"{request.url_for('course_planning_view')}?"
        + urlencode({"semester": semester, "academic_year": academic_year}),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/app/planning/review", response_class=HTMLResponse)
async def review_course_selection(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    semester: str = "Semester 1",
    academic_year: str = "2026/2027",
):
    planning = get_course_planning_data(
        CourseSelectionRepository(db),
        user.id,
        semester,
        academic_year,
    )
    return templates.TemplateResponse(
        request=request,
        name="course-review.html",
        context={"user": user, "planning": planning},
    )


@router.get("/app/planning/history", response_class=HTMLResponse)
async def course_selection_history_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    history = get_course_selection_history(CourseSelectionRepository(db), user.id)
    return templates.TemplateResponse(
        request=request,
        name="course-history.html",
        context={"user": user, "history": history},
    )


@router.post("/app/planning/history/delete", response_class=RedirectResponse)
async def delete_course_selection(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    selection_id: int = Form(),
):
    try:
        delete_course_plan(
            CourseSelectionRepository(db),
            user.id,
            selection_id,
        )
        flash(request, "Draft semester plan deleted.", "success")
    except ValueError as exc:
        flash(request, str(exc), "warning")
    return RedirectResponse(
        url=request.url_for("course_selection_history_view"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/app/planning/submit", response_class=RedirectResponse)
async def submit_course_selection(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    semester: str = Form(),
    academic_year: str = Form(),
):
    try:
        submit_course_plan(
            CourseSelectionRepository(db),
            user.id,
            semester,
            academic_year,
        )
    except ValueError as exc:
        flash(request, str(exc), "warning")
    return RedirectResponse(
        url=f"{request.url_for('review_course_selection')}?"
        + urlencode({"semester": semester, "academic_year": academic_year}),
        status_code=status.HTTP_303_SEE_OTHER,
    )
from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AdminDep
from app.dependencies.session import SessionDep
from app.repositories.course_selection import CourseSelectionRepository
from app.services.course_selection import (
    decide_course_selection,
    get_advisor_history_data,
    get_advisor_review_data,
    get_advisor_selection_data,
)
from app.utilities.flash import flash
from . import router, templates


@router.get("/advisor", response_class=HTMLResponse)
async def advisor_home_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
    search: str = "",
):
    reviews = get_advisor_review_data(CourseSelectionRepository(db), search)
    return templates.TemplateResponse(
        request=request,
        name="advisor-dashboard.html",
        context={"user": user, "reviews": reviews, "search": search},
    )


@router.get("/advisor/history", response_class=HTMLResponse)
async def advisor_history_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
    search: str = "",
):
    history = get_advisor_history_data(CourseSelectionRepository(db), search)
    return templates.TemplateResponse(
        request=request,
        name="advisor-history.html",
        context={"user": user, "history": history, "search": search},
    )


@router.get("/advisor/selection/{selection_id}", response_class=HTMLResponse)
async def advisor_selection_view(
    request: Request,
    selection_id: int,
    user: AdminDep,
    db: SessionDep,
):
    review = get_advisor_selection_data(
        CourseSelectionRepository(db),
        selection_id,
    )
    if review is None:
        return RedirectResponse(
            url=request.url_for("advisor_home_view"),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    return templates.TemplateResponse(
        request=request,
        name="advisor-review.html",
        context={"user": user, "review": review},
    )


@router.post("/advisor/selection/{selection_id}/decision")
async def advisor_decision(
    request: Request,
    selection_id: int,
    user: AdminDep,
    db: SessionDep,
    decision: str = Form(),
    advisor_comment: str = Form(default=""),
):
    try:
        decide_course_selection(
            CourseSelectionRepository(db),
            selection_id,
            decision,
            advisor_comment,
        )
        flash(request, f"Semester plan {decision}.", "success")
    except ValueError as exc:
        flash(request, str(exc), "warning")
    return RedirectResponse(
        url=request.url_for("advisor_home_view"),
        status_code=status.HTTP_303_SEE_OTHER,
    )

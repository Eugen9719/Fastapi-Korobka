from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from backend.app.api.stadiums_api import get_stadiums, get_stadium
from backend.app.models import Stadiums
from backend.app.models.stadiums import StadiumsRead

from backend.app.repositories.user_repositories import user_repo
from backend.core.db import SessionDep

page_router = APIRouter()
templates = Jinja2Templates(directory="backend/templates")


@page_router.get("/login", response_class=HTMLResponse)
async def login(request: Request, ):
    return templates.TemplateResponse("login.html", {"request": request, })


@page_router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    return templates.TemplateResponse("profile.html", {
        "request": request,

    })


@page_router.get("/chat", response_class=HTMLResponse)
async def chat(request: Request, db: SessionDep):
    return templates.TemplateResponse("chat.html", {
        "request": request,

    })


@page_router.get("/detail/{stadium_slug}", response_class=HTMLResponse)
async def detail_stadium(request: Request, stadium: StadiumsRead = Depends(get_stadium), ):
    return templates.TemplateResponse("detail.html", {
        "request": request,"stadium": stadium,

    })


@page_router.get("/", response_class=HTMLResponse)
async def index(request: Request, stadiums: List[StadiumsRead] = Depends(get_stadiums)):
    return templates.TemplateResponse("index.html", {"request": request, "stadiums": stadiums})

# @router.get("/", response_class=HTMLResponse, summary="Chat Page")
# async def get_chat_page(request: Request, user_data: User = Depends(get_current_user)):
#     users_all = await UsersDAO.find_all()
#     return templates.TemplateResponse("chat.html",
#                                       {"request": request, "user": user_data, 'users_all': users_all})

# @page_router.get("/profile", response_class=HTMLResponse)
# async def profile(request: Request,db: SessionDep, user=Depends(user_me) ):
#     bookings = db.query(Booking).filter(Booking.user_id == user.id).all()
#     return templates.TemplateResponse("profile.html", {
#         "request": request,
#         "user": user,
#         "bookings": bookings
#     })

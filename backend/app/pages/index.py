from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.requests import Request
from starlette.templating import Jinja2Templates

# from backend.app.api.stadiums_api import get_stadiums, get_stadium
# from backend.app.models import Stadium
# from backend.app.models.stadiums import StadiumsRead
#
# from backend.app.repositories.user_repositories import user_repo
from backend.core.db import SessionDep

page_router = APIRouter()
templates = Jinja2Templates(directory="backend/templates")

#
# @page_router.get("/login", response_class=HTMLResponse)
# async def login(request: Request, ):
#     return templates.TemplateResponse("login.html", {"request": request, })
#
#
# @page_router.get("/profile", response_class=HTMLResponse)
# async def profile(request: Request):
#     return templates.TemplateResponse("profile.html", {
#         "request": request,
#
#     })
#
#
# @page_router.get("/chat", response_class=HTMLResponse)
# async def chat(request: Request, db: SessionDep):
#     return templates.TemplateResponse("chat.html", {
#         "request": request,
#
#     })
#
#
# @page_router.get("/detail/{stadium_slug}", response_class=HTMLResponse)
# async def detail_stadium(request: Request, stadium: StadiumsRead = Depends(get_stadium), ):
#     return templates.TemplateResponse("detail.html", {
#         "request": request,"stadium": stadium,
#
#     })
# @page_router.get("/vendor-profile", response_class=HTMLResponse)
# async def example(request: Request, ):
#     return templates.TemplateResponse("vendor-profile/index.html", {"request": request,})
#
# @page_router.get("/", response_class=HTMLResponse)
# async def index(request: Request, stadiums: List[StadiumsRead] = Depends(get_stadiums)):
#     return templates.TemplateResponse("index.html", {"request": request, "stadiums": stadiums})
#
#
# @page_router.get("/checkout", response_class=HTMLResponse)
# async def checkout(request: Request):
#     return templates.TemplateResponse("checkout.html", {"request": request,})
#
#
# @page_router.get("/vendor-profile", response_class=HTMLResponse)
# async def vendor_profile(request: Request, ):
#     return templates.TemplateResponse("vendor-profile/index.html", {"request": request,})
# @page_router.get("/vendor-profile/stadiums", response_class=HTMLResponse)
# async def vendor_profile_stadiums(request: Request, ):
#     return templates.TemplateResponse("vendor-profile/page-stadiums.html", {"request": request,})
# @page_router.get("/vendor-profile/bookings", response_class=HTMLResponse)
# async def vendor_profile_bookings(request: Request, ):
#     return templates.TemplateResponse("vendor-profile/page-bookings.html", {"request": request,})
# @page_router.get("/vendor-profile/booking/{booking_id}", response_class=HTMLResponse)
# async def vendor_detail_bookings(request: Request, ):
#     return templates.TemplateResponse("vendor-profile/page-booking-detail.html", {"request": request,})
# @page_router.get("/vendor-profile/add-stadium", response_class=HTMLResponse)
# async def vendor_profile_add_stadium(request: Request, ):
#     return templates.TemplateResponse("vendor-profile/page-add-stadium.html", {"request": request,})
# @page_router.get("/vendor-profile/update-stadium/{stadium_id}", response_class=HTMLResponse)
# async def vendor_profile_update_stadium(request: Request):
#     return templates.TemplateResponse("vendor-profile/update-stadium.html", {"request": request,})
#
# @page_router.get("/vendor-profile/account", response_class=HTMLResponse)
# async def vendor_profile_account(request: Request):
#     return templates.TemplateResponse("vendor-profile/page-account.html", {"request": request,})
# @page_router.get("/vendor-profile/reset-password", response_class=HTMLResponse)
# async def vendor_profile_reset_password(request: Request):
#     return templates.TemplateResponse("vendor-profile/reset-password.html", {"request": request,})
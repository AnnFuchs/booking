from fastapi import APIRouter

from src.auth.router import router as auth_router
from src.bookings.router import router as booking_router
from src.cafes.router import router as cafes_router
from src.media.router import router as media_router
from src.slots.router import router as slots_router
from src.tables.router import router as tables_router
from src.users.router import router as users_router

main_router = APIRouter()

main_router.include_router(auth_router)
main_router.include_router(users_router)
main_router.include_router(media_router)
main_router.include_router(booking_router)

main_router.include_router(cafes_router)
main_router.include_router(tables_router)
main_router.include_router(slots_router)

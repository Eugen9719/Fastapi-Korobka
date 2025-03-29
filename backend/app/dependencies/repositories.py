from backend.app.repositories.bookings_repositories import BookingRepository
from backend.app.repositories.chat_repositories import MessageRepositories
from backend.app.repositories.facility_repository import FacilityRepository
from backend.app.repositories.review_repository import ReviewRepository
from backend.app.repositories.stadiums_repositories import StadiumRepository
from backend.app.repositories.user_repositories import UserRepository
from backend.app.repositories.verification_repository import VerifyRepository

user_repo = UserRepository()
verify_repo = VerifyRepository()
review_repo = ReviewRepository()
facility_repo = FacilityRepository()
stadium_repo = StadiumRepository()
booking_repo = BookingRepository()
message_repo = MessageRepositories()
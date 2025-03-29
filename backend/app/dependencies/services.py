from backend.app.dependencies.repositories import stadium_repo, review_repo, facility_repo, booking_repo, user_repo, verify_repo
from backend.app.models import Stadium, User
from backend.app.services.auth.authentication import UserAuthentication
from backend.app.services.auth.password_service import PasswordService
from backend.app.services.auth.permission import PermissionService
from backend.app.services.auth.registration_service import RegistrationService
from backend.app.services.auth.user_service import UserService
from backend.app.services.booking.booking_service import BookingService
from backend.app.services.email.email_service import EmailService
from backend.app.services.facility.facility_service import FacilityService
from backend.app.services.image.image_service import CloudinaryImageHandler
from backend.app.services.redis import RedisClient
from backend.app.services.review.review_service import ReviewService
from backend.app.services.stadium.stadium_service import StadiumService


password_service = PasswordService()
email_service = EmailService()
permission_service = PermissionService()
redis_client = RedisClient("redis://redis:6379")

review_service = ReviewService(stadium_repo, review_repo, permission_service, redis_client)
stadium_service = StadiumService(stadium_repo,  permission_service, redis_client,CloudinaryImageHandler(Stadium))
facility_service = FacilityService(facility_repo, permission_service)
booking_service = BookingService(booking_repo,stadium_repo,facility_repo, permission_service )


user_auth = UserAuthentication(password_service, user_repo)
registration_service = RegistrationService(user_repo, verify_repo, email_service, password_service)
user_service = UserService(user_repo,permission_service,password_service,email_service,CloudinaryImageHandler(User))









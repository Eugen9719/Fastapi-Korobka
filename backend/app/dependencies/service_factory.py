from typing import Type

from sqlmodel import SQLModel

from backend.app.interface.repositories.i_booking_repo import IBookingRepository
from backend.app.interface.repositories.i_facility_repo import IFacilityRepository
from backend.app.interface.repositories.i_review_repo import IReviewRepository
from backend.app.interface.repositories.i_stadium_repo import IStadiumRepository
from backend.app.interface.repositories.i_user_repo import IUserRepository
from backend.app.interface.repositories.i_verification_repo import IVerifyRepository
from backend.app.interface.utils.i_password_service import IPasswordService
from backend.app.models import Stadium, User
from backend.app.repositories.bookings_repositories import BookingRepository
from backend.app.repositories.chat_repositories import MessageRepositories
from backend.app.repositories.facility_repository import FacilityRepository
from backend.app.repositories.review_repository import ReviewRepository
from backend.app.repositories.stadiums_repositories import StadiumRepository
from backend.app.repositories.user_repositories import UserRepository
from backend.app.repositories.verification_repository import VerifyRepository
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
from backend.app.services.stadium.stadium_intervals_service import StadiumIntervalsService
from backend.app.services.stadium.stadium_service import StadiumService
from backend.app.services.stadium.stadium_verif_service import StadiumVerifService


class ServiceFactory:
    def __init__(self,redis_url: str = "redis://redis:6379"):
        # Инициализация репозиториев
        self._user_repo = UserRepository()
        self._verify_repo = VerifyRepository()
        self._review_repo = ReviewRepository()
        self._facility_repo = FacilityRepository()
        self._stadium_repo = StadiumRepository()
        self._booking_repo = BookingRepository()
        self._message_repo = MessageRepositories()

        # Базовые сервисы
        self._password_service = PasswordService()
        self._email_service = EmailService()
        self._permission_service = PermissionService()
        self._redis_client = RedisClient(redis_url)
        self._image_handlers: dict[Type[SQLModel], CloudinaryImageHandler] = {}

        # Лениво инициализируемые сервисы
        self._review_service = None

        self._facility_service = None
        self._booking_service = None
        self._user_auth = None
        self._registration_service = None
        self._user_service = None

        self._stadium_service = None
        self._stadium_verif_service = None
        self._stadium_intervals_service = None


    def get_image_handler(self, model_type: Type[SQLModel]) -> CloudinaryImageHandler:
        if model_type not in self._image_handlers:
            self._image_handlers[model_type] = CloudinaryImageHandler(model_type)
        return self._image_handlers[model_type]

    # --- Core Services ---
    @property
    def password_service(self) -> IPasswordService:
        return self._password_service

    @property
    def email_service(self) -> EmailService:
        return self._email_service

    @property
    def permission_service(self) -> PermissionService:
        return self._permission_service

    @property
    def redis_client(self) -> RedisClient:
        return self._redis_client



    # --- Repository Access ---
    @property
    def user_repo(self) -> IUserRepository:
        return self._user_repo

    @property
    def stadium_repo(self) -> IStadiumRepository:
        return self._stadium_repo

    @property
    def booking_repo(self) -> IBookingRepository:
        return self._booking_repo

    @property
    def verify_repo(self) -> IVerifyRepository:
        return self._verify_repo

    @property
    def review_repo(self) -> IReviewRepository:
        return self._review_repo

    @property
    def facility_repo(self) -> IFacilityRepository:
        return self._facility_repo

    @property
    def message_repo(self) -> MessageRepositories:
        return self._message_repo



    # --- Business Services ---
    @property
    def review_service(self) -> ReviewService:
        if self._review_service is None:
            self._review_service = ReviewService(
                stadium_repository=self._stadium_repo,
                review_repository=self._review_repo,
                permission=self._permission_service,
                redis=self._redis_client
            )
        return self._review_service

    ############# Stadium #########################
    @property
    def stadium_service(self) -> StadiumService:
        if self._stadium_service is None:
            self._stadium_service = StadiumService(
                stadium_repository=self._stadium_repo,
                permission=self._permission_service,
                redis=self._redis_client,
                image_handler=self.get_image_handler(Stadium)
            )
        return self._stadium_service

    @property
    def stadium_verif_service(self) -> StadiumVerifService:
        if self._stadium_verif_service is None:
            self._stadium_verif_service = StadiumVerifService(
                stadium_repository=self._stadium_repo,
                permission=self._permission_service,
                redis=self._redis_client
            )
        return self._stadium_verif_service

    @property
    def stadium_intervals_service(self) -> StadiumIntervalsService:
        if self._stadium_verif_service is None:
            self._stadium_verif_service = StadiumIntervalsService(
                stadium_repository=self._stadium_repo,
                permission=self._permission_service,
                redis=self._redis_client
            )
        return self._stadium_verif_service

    ##############################################
    @property
    def facility_service(self) -> FacilityService:
        if self._facility_service is None:
            self._facility_service = FacilityService(
                facility_repository=self._facility_repo,
                permission=self._permission_service
            )
        return self._facility_service

    @property
    def booking_service(self) -> BookingService:
        if self._booking_service is None:
            self._booking_service = BookingService(
                booking_repository=self._booking_repo,
                stadium_repository=self._stadium_repo,
                facility_repository=self._facility_repo,
                permission=self._permission_service
            )
        return self._booking_service


    ################# User ####################
    @property
    def user_auth(self) -> UserAuthentication:
        if self._user_auth is None:
            self._user_auth = UserAuthentication(
                pass_service=self._password_service,
                user_repository=self._user_repo
            )
        return self._user_auth

    @property
    def registration_service(self) -> RegistrationService:
        if self._registration_service is None:
            self._registration_service = RegistrationService(
                user_repository=self._user_repo,
                verif_repository=self._verify_repo,
                email_service=self._email_service,
                pass_service=self._password_service
            )
        return self._registration_service

    @property
    def user_service(self) -> UserService:
        if self._user_service is None:
            self._user_service = UserService(
                user_repository=self._user_repo,
                permission=self._permission_service,
                pass_service=self._password_service,
                email_service=self._email_service,
                image_handler=self.get_image_handler(User)
            )
        return self._user_service





service_factory = ServiceFactory()

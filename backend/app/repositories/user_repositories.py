from sqlmodel import select, Session

from backend.app.models.users import User, UserCreateAdmin, UserUpdateAdmin, UserCreate, UserUpdate, StatusEnum
from backend.app.repositories.base_repositories import BaseRepository
from backend.core.security import verify_password, get_password_hash


class UserRepositoryAdmin(BaseRepository[User, UserCreateAdmin, UserUpdateAdmin]):
    def create_user(self, db: Session, schema: UserCreateAdmin, **kwargs):
        hashed_password = get_password_hash(schema.password)
        # Передаём хэшированный пароль в kwargs
        return super().create(db, schema, hashed_password=hashed_password, **kwargs)


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):

    def get_by_email(self, db: Session, email: str):
        return db.exec(select(self.model).where(self.model.email == email)).first()

    def create(self, db: Session, *args, schema: UserCreate, **kwargs):
        hashed_password = get_password_hash(schema.password)
        return super().create(db, schema, hashed_password=hashed_password, **kwargs)

    def authenticate(self, db: Session, email: str, password: str) -> User | None:
        db_user = self.get_by_email(db=db, email=email)
        if not db_user:
            return None
        if not verify_password(password, db_user.hashed_password):
            return None
        return db_user


    def update_password(self, db: Session, obj: User, hashed_password: str):
        obj.hashed_password = hashed_password
        self.save_db(db, obj)

    @staticmethod
    def is_active(model: User) -> bool:
        return model.is_active

    @staticmethod
    def is_superuser(model: User) -> bool:
        return model.is_superuser

    @staticmethod
    def is_owner(model: User):
        if model.status == StatusEnum.OWNER:
            return True


user_repository = UserRepository(User)
admin_user_repository = UserRepositoryAdmin(User)

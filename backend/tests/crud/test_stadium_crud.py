import pytest
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.dependencies.repositories import user_repo, stadium_repo, review_repo
from backend.app.dependencies.services import stadium_service, review_service
from backend.app.models.stadiums import StadiumsCreate, StadiumsUpdate, StadiumStatus, StadiumVerificationUpdate, \
    CreateReview, UpdateReview


@pytest.mark.anyio
@pytest.mark.usefixtures("db", "test_data")
class TestCrudStadium:
    @pytest.mark.parametrize("user_id, slug, expected_exception, status_code, detail", [
        (1, "slug", None, None, None),
        (1, "slug", HTTPException, 400, "Слаг уже используется")
    ])
    async def test_create_stadium(self, db: AsyncSession, user_id, slug, expected_exception, status_code, detail):
        # Получаем пользователя
        user = await user_repo.get_or_404(db, id=user_id)

        # Создаем схему стадиона
        create_schema = StadiumsCreate(
            name="name",
            slug=slug,
            address="address",
            price=100,
            country="country",
            city="city",
        )

        if expected_exception:
            with pytest.raises(expected_exception) as exc_info:
                await stadium_service.create_stadium(db=db, schema=create_schema, user=user)
            assert exc_info.value.status_code == status_code
            assert exc_info.value.detail == detail
        else:
            stadium = await stadium_service.create_stadium(db=db, schema=create_schema, user=user)
            assert stadium is not None
            assert stadium.slug == create_schema.slug

            # Проверяем сохранение в БД
            saved_stadium = await stadium_repo.get(db, id=stadium.id)
            assert saved_stadium is not None



    @pytest.mark.parametrize("user_id, slug, stadium_id, expected_exception, status_code, detail", [
        (2, "slug45", 3, HTTPException, 403, "Только админ или создатель могут проводить операции"),
        (1,"otkritiecrud",3, HTTPException, 400, "вы не можете изменить объект, пока у него статус 'На верификации'"  ),
        (1, "otkritiecrud", 6, HTTPException, 400, "Слаг уже используется"),  # создатель обновляет
        (1, "slug", 6, None, None, None),  # создатель обновляет
        (3, "slug1", 6, None, None, None),  # админ обновляет
    ])
    async def test_update_stadium(self, db: AsyncSession, user_id, slug, stadium_id, expected_exception, status_code,
                                  detail):
        user = await user_repo.get_or_404(db=db, id=user_id)
        update_schema = StadiumsUpdate(
            name="new_name",
            slug=slug,
            address="new_address",
            price=2000,
            country="new_country",
            city="new_city",
        )

        if expected_exception:
            with pytest.raises(expected_exception) as exc_info:
                await stadium_service.update_stadium(db, schema=update_schema, stadium_id=stadium_id, user=user)
            assert exc_info.value.status_code == status_code
            assert exc_info.value.detail == detail
        else:
            await stadium_service.update_stadium(db, schema=update_schema, stadium_id=stadium_id, user=user)
            updated_stadium = await stadium_repo.get_or_404(db=db, id=stadium_id)

            assert updated_stadium.slug == update_schema.slug

    @pytest.mark.parametrize("user_id,stadium_id,expected_exception,status_code,detail", [
        (1, 99, HTTPException, 404, "Объект не найден"),
        (1, 5, HTTPException, 400, "вы не можете изменить объект, пока у него статус 'На верификации'"),
        (2, 1, HTTPException, 403, "Только админ или создатель могут проводить операции"),
        (1, 2, None, None, None),
    ])
    async def test_verif_stadium(self, db, user_id, stadium_id, expected_exception, status_code, detail, mock_redis):
        user = await user_repo.get_or_404(db=db, id=user_id)

        update_schema = StadiumVerificationUpdate(
            status=StadiumStatus.VERIFICATION
        )

        if expected_exception:
            with pytest.raises(expected_exception) as exc_info:
                await stadium_service.verify_stadium(db, schema=update_schema, stadium_id=stadium_id, user=user)
            assert exc_info.value.status_code == status_code
            assert exc_info.value.detail == detail
            # Убедимся, что redis не вызывался при ошибках
            mock_redis.invalidate_cache.assert_not_called()
        else:
            await stadium_service.verify_stadium(db, schema=update_schema, stadium_id=stadium_id, user=user)

            # Проверяем правильные вызовы инвалидации кеша
            mock_redis.invalidate_cache.assert_any_await(
                f"stadiums:vendor:{user.id}",
                f"Обновление стадиона {stadium_id}"
            )





            updated_stadium = await stadium_repo.get_or_404(db=db, id=stadium_id)

            assert updated_stadium.status == update_schema.status

    @pytest.mark.parametrize("user_id,stadium_id,expected_exception, status_code, detail", [
        (3, 99, HTTPException, 404, "Объект не найден"),
        (3, 5, None, None, None),

    ])
    async def test_approve_verification(self, db, user_id, stadium_id, expected_exception, status_code, detail):

        user = await user_repo.get_or_404(db=db, id=user_id)
        update_schema = StadiumVerificationUpdate(
            status=StadiumStatus.ADDED
        )

        if expected_exception:
            with pytest.raises(expected_exception) as exc_info:
                await stadium_service.approve_verification_by_admin(db, schema=update_schema, stadium_id=stadium_id, user=user)
            assert exc_info.value.status_code == status_code
            assert exc_info.value.detail == detail
        else:
            await stadium_service.approve_verification_by_admin(db, schema=update_schema, stadium_id=stadium_id, user=user)
            updated_stadium = await stadium_repo.get_or_404(db=db, id=stadium_id)

            assert updated_stadium.status == update_schema.status
            assert updated_stadium.is_active == True



@pytest.mark.usefixtures("db", "test_data")
@pytest.mark.anyio
class TestCrudReview:
    @pytest.mark.parametrize("user_id, stadium_id, expected_exception, status_code, detail", [
        (1, 1, None, None, None),
        (1, 1, HTTPException, 400, "Вы уже оставили отзыв для этого стадиона")
    ])
    async def test_create_review(self, db: AsyncSession, user_id, stadium_id, expected_exception, status_code, detail):
        user = await user_repo.get_or_404(db=db, id=user_id)
        create_schema = CreateReview(review="fdhgsfh")

        # Выполняем создание отзыва
        if expected_exception:
            # Проверяем, что выбрасывается ожидаемое исключение
            with pytest.raises(expected_exception) as exc_info:
                await review_service.create_review(db=db, schema=create_schema, stadium_id=stadium_id, user=user)

            # Проверяем атрибуты исключения
            assert exc_info.value.status_code == status_code
            assert exc_info.value.detail == detail
        else:
            # Если исключение не ожидается, проверяем создание отзыва
            review = await review_service.create_review(db=db, schema=create_schema, stadium_id=stadium_id, user=user)

            # Проверяем, что отзыв действительно создан и попал в базу данных
            assert review is not None
            assert review.review == create_schema.review

            # Проверка, что запись появилась в БД
            created_review = await review_repo.get_or_404(db=db, id=review.id)
            assert created_review is not None
            assert created_review.review == create_schema.review

    async def test_update_review(self, db: AsyncSession):

        user = await user_repo.get_or_404(db=db, id=1)
        update_schema = UpdateReview(
            review="fdhgsfh"
        )
        await review_service.update_review(db, schema=update_schema, user=user, review_id=3)
        updated_review = await review_repo.get_or_404(db=db, id=3)
        assert updated_review.review == update_schema.review

    async def test_delete_review(self, db: AsyncSession):
        user = await user_repo.get_or_404(db=db, id=1)
        response = await review_service.delete_review(db, review_id=3, user=user)
        # Проверяем результат
        assert response.msg == "отзыв успешно удален"

        # Проверяем, что стадион больше не существует в базе
        with pytest.raises(HTTPException) as exc_info:
            await review_repo.get_or_404(db=db, id=3)
        assert exc_info.value.status_code == 404

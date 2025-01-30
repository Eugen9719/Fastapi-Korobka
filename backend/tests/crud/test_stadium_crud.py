import pytest
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.models.stadiums import StadiumsCreate, StadiumsUpdate, StadiumStatus, StadiumVerificationUpdate, \
    CreateReview, UpdateReview
from backend.app.repositories.stadiums_repositories import stadium_repo, review_repo
from backend.app.repositories.user_repositories import user_repo


@pytest.mark.run(order=1)
@pytest.mark.anyio
class TestCrudStadium:
    @pytest.mark.parametrize("user_id, slug, expected_exception, status_code, detail", [
        (1, "slug", None, None, None),
        (1, "slug", HTTPException, 400, "Slug already used")  # email уже занят
    ])
    async def test_create_stadium(self, db: AsyncSession, user_id, slug, expected_exception, status_code, detail):
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
                await stadium_repo.create_stadium(db=db, schema=create_schema, user_id=user_id)
            assert exc_info.value.status_code == status_code
            assert exc_info.value.detail == detail
        else:
            await stadium_repo.create_stadium(db=db, schema=create_schema, user_id=user_id)

    @pytest.mark.parametrize("user_id, slug, stadium_id, expected_exception, status_code, detail", [
        (2, "slug", 3, HTTPException, 403, "Только админ или создатель могут проводить операции"),
        (1, "slug", 3, None, None, None),  # создатель обновляет
        (3, "slug1", 3, None, None, None),  # админ обновляет
    ])
    async def test_update_stadium(self, db: AsyncSession, user_id, slug, stadium_id, expected_exception, status_code,
                                  detail):

        user = await user_repo.get_user_by_id(db=db, user_id=user_id)
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
                await stadium_repo.update_stadium(db, schema=update_schema, stadium_id=stadium_id, user=user)
            assert exc_info.value.status_code == status_code
            assert exc_info.value.detail == detail
        else:
            await stadium_repo.update_stadium(db, schema=update_schema, stadium_id=stadium_id, user=user)
            updated_stadium = await stadium_repo.get_or_404(db=db, id=stadium_id)

            assert updated_stadium.slug == update_schema.slug

    async def test_verif_stadium(self, db: AsyncSession):

        # user = await user_repo.get_user_by_id(db=db, user_id=3)
        update_schema = StadiumVerificationUpdate(
            status="added"
        )
        await stadium_repo.verification(db, schema=update_schema, stadium_id=3)

        updated_stadium = await stadium_repo.get_or_404(db=db, id=3)

        assert updated_stadium.status == StadiumStatus.ADDED
        assert updated_stadium.is_active is True

    async def test_delete_stadium(self, db: AsyncSession, ):
        user = await user_repo.get_user_by_id(db=db, user_id=1)
        response = await stadium_repo.delete_stadium(db, stadium_id=3, user=user)
        # Проверяем результат
        assert response.msg == "stadium deleted successfully"

        # Проверяем, что стадион больше не существует в базе
        with pytest.raises(HTTPException) as exc_info:
            await stadium_repo.get_or_404(db=db, id=3)
        assert exc_info.value.status_code == 404


@pytest.mark.run(order=1)
@pytest.mark.anyio
class TestCrudReview:
    @pytest.mark.parametrize("user_id, stadium_id, expected_exception, status_code, detail", [
        (1, 1, None, None, None),
        (1, 1, HTTPException, 400, "Вы уже оставили отзыв для этого стадиона")
    ])
    async def test_create_review(self, db: AsyncSession, user_id, stadium_id, expected_exception, status_code, detail):
        user = await user_repo.get_user_by_id(db=db, user_id=user_id)
        create_schema = CreateReview(review="fdhgsfh")

        # Выполняем создание отзыва
        if expected_exception:
            with pytest.raises(expected_exception) as exc_info:
                await review_repo.create_review(db=db, schema=create_schema, stadium_id=stadium_id, user=user)
            assert exc_info.value.status_code == status_code
            assert exc_info.value.detail == detail
        else:
            review = await review_repo.create_review(db=db, schema=create_schema, stadium_id=stadium_id, user=user)

            # Проверяем, что отзыв действительно создан и попал в базу данных
            assert review is not None
            assert review.review == create_schema.review

            # Проверка, что запись появилась в БД
            created_review = await review_repo.get_or_404(db=db, id=review.id)
            assert created_review is not None
            assert created_review.review == create_schema.review

    async def test_update_review(self, db: AsyncSession):

        user = await user_repo.get_user_by_id(db=db, user_id=1)
        update_schema = UpdateReview(
            review="fdhgsfh"
        )
        await review_repo.update_review(db, schema=update_schema, user=user, review_id=3)
        updated_review = await review_repo.get_or_404(db=db, id=3)
        assert updated_review.review == update_schema.review

    async def test_delete_review(self, db: AsyncSession):
        user = await user_repo.get_user_by_id(db=db, user_id=1)
        response = await review_repo.delete_review(db, review_id=3, user=user)
        # Проверяем результат
        assert response.msg == "Review deleted successfully"

        # Проверяем, что стадион больше не существует в базе
        with pytest.raises(HTTPException) as exc_info:
            await review_repo.get_or_404(db=db, id=3)
        assert exc_info.value.status_code == 404

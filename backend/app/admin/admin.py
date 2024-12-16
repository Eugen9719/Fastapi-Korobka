from sqladmin import ModelView


from backend.app.models.users import User


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email]
    column_details_exclude_list = [User.hashed_password]
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"


# class CategoryAdmin(ModelView, model=Category):
#     column_list = [Category.id, Category.name, Category.slug, Category.parent, Category.updated_at, Category.image]
#     name_plural = "Категории"
#
#
# class CategoryImageAdmin(ModelView, model=CategoryImage):
#     column_list = ("id", "category_id", "image_url", "category.name")  # Поля, которые вы хотите отображать
#     name_plural = "Фото категорий"
#
#
# class ProductAdmin(ModelView, model=Product):
#     column_list = [Product.id, Product.vendor_id, Product.name, Product.price, Product.slug, Product.category_id]
#     name = "Продукт"
#     name_plural = "Продукты"
#     icon = "fa-thin fa-court-sport"

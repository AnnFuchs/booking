from src.crud.crud import CRUDBase
from src.db.models_for_alembic import Cafe


class CRUDCafe(CRUDBase[Cafe]):
    """CRUD класс для модели Cafe."""


cafe_crud = CRUDCafe(Cafe)

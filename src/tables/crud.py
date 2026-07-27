from src.crud.crud import CRUDBase
from src.db.models_for_alembic import Table


class CRUDTable(CRUDBase[Table]):
    """CRUD для Table с доменной логикой."""


table_crud = CRUDTable(Table)

from tortoise.fields.base import Field
from typing import List, Any, Optional, Union, Type
from tortoise.models import Model


class BigIntArrayField(Field, list):
    SQL_TYPE = "bigint[]"

    def to_db_value(self, value: Any, instance: Union[Type[Model], Model]) -> Any:
        return value

    def to_python_value(self, value: Any) -> Optional[List[int]]:
        return value

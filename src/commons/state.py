import typing
from functools import total_ordering

from pydantic_core import CoreSchema, core_schema

VARIANT_STATE = typing.Literal["LOW", "MEDIUM", "HIGH", "UNSTAGED"]


@total_ordering
class State:
    """
    State class for traffic state.
    """

    def __init__(self, state: VARIANT_STATE) -> None:
        self.state = state
        self.compare_value = {
            "UNSTAGED": -1,
            "LOW": 0,
            "MEDIUM": 1,
            "HIGH": 2,
        }

    def __eq__(self, other: object) -> bool:
        if isinstance(other, State):
            return self.state == other.state
        if isinstance(other, str):
            return self.state == other
        return NotImplemented

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, str):
            return NotImplemented
        if other not in self.compare_value:
            return NotImplemented
        return self.compare_value[self.state] > self.compare_value[other]

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, str):
            return NotImplemented
        if other not in self.compare_value:
            return NotImplemented
        return self.compare_value[self.state] < self.compare_value[other]

    @property
    def value(self) -> str:
        return self.state

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: typing.Any, _handler: typing.Any) -> CoreSchema:
        """Get Pydantic core schema."""
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(cls),
                    core_schema.str_schema(),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: x.value if isinstance(x, cls) else x
            ),
        )

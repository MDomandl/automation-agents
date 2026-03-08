from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Result(Generic[T]):
    value: T | None = None
    error: str | None = None

    @property
    def is_ok(self) -> bool:
        return self.error is None

    @staticmethod
    def ok(value: T) -> "Result[T]":
        return Result(value=value)

    @staticmethod
    def fail(error: str) -> "Result[T]":
        return Result(error=error)
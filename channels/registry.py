from abc import ABC, abstractmethod
from typing import Callable

_registry: dict[str, "BaseChannel"] = {}

class BaseChannel(ABC):
    name: str

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "name"):
            _registry[cls.name] = cls()

    @abstractmethod
    async def start(self, on_message: Callable): ...

    @abstractmethod
    async def send(self, group_id: str, text: str): ...

def get_active() -> list["BaseChannel"]:
    return list(_registry.values())

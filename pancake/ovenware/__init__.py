from pancake import oven
import builtins
import logging

builtins.__dict__["oven"] = oven
builtins.__dict__["logging"] = logging

from abc import ABC, abstractmethod

class InitAction(ABC):

    name : str = "InitAction"

    init_order : int = 0
    build_order : int = 0

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def build(self):
        pass


class Decorator(ABC):

    @abstractmethod
    def build(self):
        pass

builtins.__dict__["InitAction"] = InitAction
builtins.__dict__["Decorator"] = Decorator


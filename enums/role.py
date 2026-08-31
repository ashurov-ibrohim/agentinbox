from enum import Enum

class Role(str, Enum):
    user = "user"
    model = "model"
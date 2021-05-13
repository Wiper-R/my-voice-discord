from enum import Enum


class VoiceType(Enum):
    normal = "normal"
    sequential = "sequential"
    predefined = "predefined"
    cloned = "cloned"
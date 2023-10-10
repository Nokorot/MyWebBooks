from .royalroad import (
    RoyalRoadWM,
)

_ALL_WM_CLASSES = [
    cls
    for name, cls in globals().items()
    if name.endswith("WM")
]

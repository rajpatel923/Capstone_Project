from fastapi import Request
from slowapi import Limiter


def _device_key(request: Request) -> str:
    device_id = request.path_params.get("device_id", "unknown")
    return f"device:{device_id}"


limiter = Limiter(key_func=_device_key)

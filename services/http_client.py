"""Small requests wrapper for consistent timeouts and error handling."""

from typing import Any, Optional

import requests


class HttpClient:
    """Thin HTTP client abstraction used by social services."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        return requests.get(url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        return requests.post(url, **kwargs)

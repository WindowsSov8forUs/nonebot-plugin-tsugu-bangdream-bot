'''`tsugu_api` HTTP 客户端的 `nonebot` 驱动实现'''

from json import dumps
from typing_extensions import cast

from nonebot import get_driver
from nonebot.drivers import HTTPClientMixin, HTTPClientSession

driver = get_driver()

if not isinstance(driver, HTTPClientMixin):
    raise ImportError("Current driver does not support HTTPClient")

from typing import Any
from typing_extensions import override

from nonebot.drivers import Request as NonebotRequest

from tsugu_api_core import settings
from tsugu_api_core.client import Client as _Client
from tsugu_api_core.client import Request, Response

class Client(_Client):
    _client: HTTPClientMixin = driver
    _session: HTTPClientSession
    
    @override
    def __enter__(self) -> 'Client':
        raise RuntimeError("Nonebot does not support sync request, use async with instead")
    
    @override
    async def __aenter__(self) -> 'Client':
        self._session = self._client.get_session(
            timeout=settings.timeout,
            proxy=settings.proxy if self.proxy and settings.proxy else None,
        )
        await self._session.__aenter__()
        return self
    
    @override
    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        pass
    
    @override
    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        await self._session.__aexit__(exc_type, exc_value, traceback)
    
    @override
    def request(self, request: Request) -> Response:
        raise RuntimeError("Nonebot does not support sync request, use async method instead")
    
    @override
    async def arequest(self, request: Request) -> Response:
        _request = NonebotRequest(
            request.method,
            request.url,
            params=request.params,
            data=cast(dict, dumps(request.data)) if request.data else None,
            headers=request.headers,
        )
        _response = await self._client.request(_request)
        if _response.content is None:
            raise RuntimeError("Response content is None")
        
        return Response(
            (
                _response.content if isinstance(_response.content, bytes)
                else _response.content # type: ignore
            ),
            _response.status_code,
        )
import pytest

from relink_coach.http_client import get_http_client, shutdown_http, startup_http


@pytest.mark.asyncio
async def test_shared_client_lifecycle():
    await startup_http()
    c1 = get_http_client()
    c2 = get_http_client()
    assert c1 is c2
    assert not c1.is_closed
    await shutdown_http()
    c3 = get_http_client()
    assert c3 is not c1
    await shutdown_http()

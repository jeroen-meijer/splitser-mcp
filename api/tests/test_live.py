import os

import pytest

from splitser_api import SplitserClient, SplitserConfig

pytestmark = pytest.mark.integration


@pytest.fixture
def live_config() -> SplitserConfig:
    email = os.environ.get("SPLITSER_EMAIL")
    password = os.environ.get("SPLITSER_PASSWORD")
    if not os.environ.get("RUN_INTEGRATION_TESTS") or not email or not password:
        pytest.skip("Set RUN_INTEGRATION_TESTS=1 plus SPLITSER_EMAIL/PASSWORD")
    return SplitserConfig.from_env()


@pytest.mark.asyncio
async def test_current_user(live_config: SplitserConfig) -> None:
    async with SplitserClient(live_config) as client:
        payload = await client.current_user()
    assert payload["current_user"]["email"] == live_config.email

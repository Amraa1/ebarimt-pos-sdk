"""Live integration tests for ``EbarimtApiClient`` (public OAuth2-free API).

These hit the real Ebarimt server (staging by default) over the network.
The public info endpoints no longer require an OAuth2 token, so the client
is constructed with no credentials.

Run with::

    uv run pytest -m integration tests/integration/test_integration_api.py

Set ``EBARIMT_ENV=production`` to point the suite at ``https://api.ebarimt.mn``
instead of the default staging host ``https://st-api.ebarimt.mn``.
"""

import os

import pytest

from ebarimt_pos_sdk import EbarimtApiClient, Environment, create_api_settings

# Reg numbers to try when resolving a real TIN for the merchant lookup test.
# The merchant endpoint's response model requires a populated ``data`` object,
# so we only exercise it once we have a TIN the server actually knows about.
_CANDIDATE_REG_NOS = ("УБ95051250", "АА10010110", "6019509", "2602987")


def _env() -> Environment:
    if os.getenv("EBARIMT_ENV", "staging").lower() == "production":
        return Environment.PRODUCTION
    return Environment.STAGING


def _client() -> EbarimtApiClient:
    return EbarimtApiClient(create_api_settings(_env()))


@pytest.mark.integration
def test_integration_api_targets_real_host():
    settings = create_api_settings(_env())
    assert settings.base_url in (
        "https://st-api.ebarimt.mn",
        "https://api.ebarimt.mn",
    )


@pytest.mark.integration
def test_integration_district_code_read():
    with _client() as client:
        resp = client.district_code.read()

    assert resp.status == 200
    assert len(resp.data) > 0
    first = resp.data[0]
    assert first.branch_code
    assert first.branch_name


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_district_code_aread():
    async with _client() as client:
        resp = await client.district_code.aread()

    assert resp.status == 200
    assert len(resp.data) > 0


@pytest.mark.integration
def test_integration_product_tax_code_read():
    with _client() as client:
        resp = client.product_tax_code.read()

    assert resp.status == 200
    assert len(resp.data) > 0
    first = resp.data[0]
    assert first.tax_product_code
    assert first.tax_product_name


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_product_tax_code_aread():
    async with _client() as client:
        resp = await client.product_tax_code.aread()

    assert resp.status == 200
    assert len(resp.data) > 0


@pytest.mark.integration
def test_integration_buna_read_top_level():
    with _client() as client:
        resp = client.buna.read()

    rows = resp.root
    assert len(rows) > 0
    # Each top-level row is [code, name].
    code, name = rows[0][0], rows[0][1]
    assert code
    assert name


@pytest.mark.integration
def test_integration_buna_read_drilldown():
    with _client() as client:
        top = client.buna.read()
        first_code = top.root[0][0]
        child = client.buna.read(first_code)

    # Drilling into a valid top-level code returns its sub-rows.
    assert isinstance(child.root, list)
    for row in child.root:
        assert isinstance(row, list)
        assert all(isinstance(cell, str) for cell in row)


@pytest.mark.integration
def test_integration_tin_info_read_roundtrip():
    # We don't assert "found" — an unknown regNo legitimately comes back with a
    # non-200 status. We only assert the live round-trip parses into the model.
    with _client() as client:
        resp = client.tin_info.read(_CANDIDATE_REG_NOS[0])

    assert isinstance(resp.status, int)
    assert isinstance(resp.data, str)
    assert resp.msg


@pytest.mark.integration
def test_integration_merchant_info_read():
    with _client() as client:
        tin: str | None = None
        for reg_no in _CANDIDATE_REG_NOS:
            resp = client.tin_info.read(reg_no)
            if resp.status == 200 and resp.data.isdigit():
                tin = resp.data
                break

        if tin is None:
            pytest.skip("no known reg number resolved to a TIN on this server")

        info = client.merchant_info.read(tin)

    assert info.status == 200
    assert info.data
    assert info.data.name

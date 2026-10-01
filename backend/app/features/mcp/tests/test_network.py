"""Keycloak boundary failures and real SDK HTTP handlers under application-role RLS."""

import time
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import text

from app.core.database import owner_session
from app.features.mcp.network import (
    Binding,
    KeycloakConfiguration,
    KeycloakVerifier,
    create_application,
)
from conftest import Account

ISSUER = "https://identity.example/realms/zenith"
RESOURCE = "https://zenith.example/mcp"


def configuration(user: UUID | None = None, tenant: UUID | None = None) -> KeycloakConfiguration:
    return KeycloakConfiguration(
        ISSUER,
        RESOURCE,
        "introspection",
        "fixture-secret",
        {"subject": Binding(user or uuid4(), tenant or uuid4(), 0)},
    )


def active() -> dict[str, object]:
    return {
        "active": True,
        "iss": ISSUER,
        "aud": [RESOURCE],
        "sub": "subject",
        "scope": "openid zenith:read",
        "exp": int(time.time()) + 300,
        "client_id": "approved-local-client",
        "token_type": "Bearer",
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("active", False),
        ("active", "true"),
        ("iss", "https://attacker.example"),
        ("aud", ["other-resource"]),
        ("exp", int(time.time()) - 10),
        ("exp", True),
        ("sub", "unlinked"),
        ("scope", "openid"),
        ("token_type", "refresh"),
    ],
)
async def test_invalid_identity_is_refused_before_tools(field: str, value: object) -> None:
    body = active()
    body[field] = value

    def introspect(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == ISSUER + "/protocol/openid-connect/token/introspect"
        assert request.headers["Authorization"].startswith("Basic ")
        return httpx.Response(200, json=body)

    verifier = KeycloakVerifier(configuration(), httpx.MockTransport(introspect))
    assert await verifier.verify_token("opaque-token") is None


async def test_valid_resource_and_bounded_fail_closed_provider() -> None:
    cfg = configuration()
    for response in (
        httpx.Response(302, headers={"location": "https://attacker.example"}),
        httpx.Response(503),
        httpx.Response(200, content=b"x" * 65537),
        httpx.Response(200, content=b"not-json"),
    ):
        verifier = KeycloakVerifier(cfg, httpx.MockTransport(lambda _, response=response: response))
        assert await verifier.verify_token("token") is None
    good = KeycloakVerifier(cfg, httpx.MockTransport(lambda _: httpx.Response(200, json=active())))
    token = await good.verify_token("token")
    assert token is not None and token.subject == "subject" and token.resource == RESOURCE
    assert await good.verify_token("x" * 8193) is None


@pytest.mark.parametrize(
    "url",
    [
        "http://identity.example/realms/zenith",
        "https://secret@identity.example/realms/zenith",
        "https://identity.example/realms/zenith?token=secret",
    ],
)
def test_operator_destination_cannot_embed_credentials_or_use_cleartext(url: str) -> None:
    with pytest.raises(ValueError):
        KeycloakConfiguration(url, RESOURCE, "client", "secret", configuration().bindings)


async def test_metadata_http_tool_current_authority_and_revocation(
    account: Account,
    labelled_document: UUID,
) -> None:
    revoked = False

    def introspect(_: httpx.Request) -> httpx.Response:
        body = active()
        body["active"] = not revoked
        return httpx.Response(200, json=body)

    cfg = configuration(account.admin_id, account.tenant_id)
    app = create_application(cfg, httpx.MockTransport(introspect))
    headers = {
        "Authorization": "Bearer opaque-token",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": "2026-07-28",
    }
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="https://zenith.example",
        ) as client,
    ):
        challenge = await client.post("/mcp", json={})
        assert challenge.status_code == 401
        assert "resource_metadata=" in challenge.headers["WWW-Authenticate"]
        metadata = await client.get("/.well-known/oauth-protected-resource/mcp")
        assert metadata.status_code == 200
        assert metadata.json()["resource"] == RESOURCE
        assert metadata.json()["authorization_servers"] == [ISSUER]
        initialized = await client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2026-07-28",
                    "capabilities": {},
                    "clientInfo": {"name": "local-proof", "version": "1"},
                },
            },
        )
        assert initialized.status_code == 200, initialized.text
        assert initialized.json()["result"]["protocolVersion"] == "2026-07-28"
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "zenith_get_document",
                "arguments": {"document_id": str(labelled_document)},
            },
        }
        disclosed = await client.post("/mcp", headers=headers, json=request)
        assert disclosed.status_code == 200
        assert disclosed.json()["result"]["structuredContent"]["id"] == str(labelled_document)
        async with owner_session() as session:
            await session.execute(
                text("UPDATE users SET token_version=token_version+1 WHERE id=:u"),
                {"u": account.admin_id},
            )
        invalidated = await client.post("/mcp", headers=headers, json=request)
        assert invalidated.json()["result"]["isError"]
        assert "structuredContent" not in invalidated.json()["result"]
        revoked = True
        assert (await client.post("/mcp", headers=headers, json=request)).status_code == 401


async def test_host_origin_and_size_do_not_reach_the_provider() -> None:
    calls = 0

    def introspect(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=active())

    app = create_application(configuration(), httpx.MockTransport(introspect))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="https://zenith.example",
    ) as client:
        for extra in ({"Host": "attacker.example"}, {"Origin": "https://attacker.example"}):
            response = await client.post(
                "/mcp", headers={"Authorization": "Bearer token", **extra}, json={}
            )
            assert response.status_code in {400, 403, 421}
        oversized = await client.post(
            "/mcp", headers={"Authorization": "Bearer token"}, content=b"x" * 65537
        )
        assert oversized.status_code == 413
        assert calls == 0

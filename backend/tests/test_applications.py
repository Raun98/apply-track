"""
Integration tests for the /applications CRUD API.
"""
import pytest


async def _register_and_token(client, email="apps@test.com"):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1"},
    )
    return reg.json()["access_token"]


async def test_create_application(client):
    token = await _register_and_token(client)
    resp = await client.post(
        "/api/v1/applications",
        json={"company_name": "Acme", "position_title": "Engineer"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["company_name"] == "Acme"
    assert data["status"] == "applied"


async def test_list_applications_empty(client):
    token = await _register_and_token(client, "list_empty@test.com")
    resp = await client.get(
        "/api/v1/applications",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


async def test_list_applications_with_data(client):
    token = await _register_and_token(client, "list_data@test.com")
    for company in ["Alpha", "Beta", "Gamma"]:
        await client.post(
            "/api/v1/applications",
            json={"company_name": company, "position_title": "Dev"},
            headers={"Authorization": f"Bearer {token}"},
        )
    resp = await client.get(
        "/api/v1/applications",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.json()["total"] == 3


async def test_list_applications_search_filter(client):
    token = await _register_and_token(client, "search@test.com")
    await client.post(
        "/api/v1/applications",
        json={"company_name": "TargetCorp", "position_title": "Manager"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/api/v1/applications",
        json={"company_name": "OtherCorp", "position_title": "Analyst"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        "/api/v1/applications?search=Target",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["company_name"] == "TargetCorp"


async def test_list_applications_status_filter(client):
    token = await _register_and_token(client, "status_filter@test.com")
    await client.post(
        "/api/v1/applications",
        json={"company_name": "Co1", "position_title": "Dev", "status": "interview"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/api/v1/applications",
        json={"company_name": "Co2", "position_title": "Dev", "status": "rejected"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        "/api/v1/applications?status=interview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.json()["total"] == 1


async def test_get_application(client):
    token = await _register_and_token(client, "get_app@test.com")
    created = await client.post(
        "/api/v1/applications",
        json={"company_name": "GetCo", "position_title": "Lead"},
        headers={"Authorization": f"Bearer {token}"},
    )
    app_id = created.json()["id"]
    resp = await client.get(
        f"/api/v1/applications/{app_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == app_id


async def test_get_application_not_found(client):
    token = await _register_and_token(client, "get_notfound@test.com")
    resp = await client.get(
        "/api/v1/applications/99999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_update_application_status(client):
    token = await _register_and_token(client, "update@test.com")
    created = await client.post(
        "/api/v1/applications",
        json={"company_name": "UpdCo", "position_title": "Dev"},
        headers={"Authorization": f"Bearer {token}"},
    )
    app_id = created.json()["id"]
    resp = await client.patch(
        f"/api/v1/applications/{app_id}",
        json={"status": "interview"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "interview"


async def test_delete_application(client):
    token = await _register_and_token(client, "delete@test.com")
    created = await client.post(
        "/api/v1/applications",
        json={"company_name": "DelCo", "position_title": "Dev"},
        headers={"Authorization": f"Bearer {token}"},
    )
    app_id = created.json()["id"]
    del_resp = await client.delete(
        f"/api/v1/applications/{app_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_resp.status_code == 204
    get_resp = await client.get(
        f"/api/v1/applications/{app_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 404


async def test_applications_isolated_between_users(client):
    token_a = await _register_and_token(client, "usera@test.com")
    token_b = await _register_and_token(client, "userb@test.com")

    created = await client.post(
        "/api/v1/applications",
        json={"company_name": "PrivateCo", "position_title": "Dev"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    app_id = created.json()["id"]

    # User B cannot access User A's application
    resp = await client.get(
        f"/api/v1/applications/{app_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 404


async def test_status_history_created_on_update(client):
    token = await _register_and_token(client, "history@test.com")
    created = await client.post(
        "/api/v1/applications",
        json={"company_name": "HistCo", "position_title": "Dev"},
        headers={"Authorization": f"Bearer {token}"},
    )
    app_id = created.json()["id"]
    await client.patch(
        f"/api/v1/applications/{app_id}",
        json={"status": "screening"},
        headers={"Authorization": f"Bearer {token}"},
    )
    hist = await client.get(
        f"/api/v1/applications/{app_id}/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert hist.status_code == 200
    entries = hist.json()
    assert len(entries) == 1
    assert entries[0]["from_status"] == "applied"
    assert entries[0]["to_status"] == "screening"

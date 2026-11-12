import pytest


@pytest.mark.asyncio
async def test_list_items_empty(client, db_session, fake_admin):
    resp = await client.get("/items")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_item(client, db_session, fake_admin):
    resp = await client.post(
        "/items",
        json={"name": "Energy Drink", "cost_credits": 5, "stock_qty": 10},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Energy Drink"
    assert data["cost_credits"] == 5
    assert data["stock_qty"] == 10


@pytest.mark.asyncio
async def test_list_items_after_create(client, db_session, fake_admin):
    await client.post(
        "/items",
        json={"name": "Water Bottle", "cost_credits": 2, "stock_qty": 20},
    )
    resp = await client.get("/items")
    assert resp.status_code == 200
    names = [i["name"] for i in resp.json()]
    assert "Water Bottle" in names

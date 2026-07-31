"""Expense CRUD and the category spending summary"""
import datetime


def test_list_expenses_requires_auth(client):
    res = client.get("/api/expenses")
    assert res.status_code == 401


def test_create_expense_rejects_invalid_category(client, auth_headers):
    res = client.post("/api/expenses", headers=auth_headers, json={
        "amount": 10, "category_id": 9999, "date": "2026-07-01", "description": "Bad category",
    })
    assert res.status_code == 400


def test_create_expense_rejects_non_positive_amount(client, auth_headers, category):
    res = client.post("/api/expenses", headers=auth_headers, json={
        "amount": 0, "category_id": category["id"], "date": "2026-07-01",
    })
    assert res.status_code == 400


def test_create_and_list_expense(client, auth_headers, category):
    create_res = client.post("/api/expenses", headers=auth_headers, json={
        "amount": 42.50, "category_id": category["id"], "date": "2026-07-01", "description": "Weekly shop",
    })
    assert create_res.status_code == 201
    created = create_res.get_json()
    assert created["amount"] == 42.50
    assert created["category_name"] == category["name"]

    list_res = client.get("/api/expenses", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.get_json()) == 1


def test_expenses_are_scoped_to_the_owning_user(client, auth_headers, category):
    client.post("/api/expenses", headers=auth_headers, json={
        "amount": 10, "category_id": category["id"], "date": "2026-07-01",
    })

    # A second, different user should not see the first user's expenses.
    client.post("/api/auth/register", json={
        "name": "Other Student", "email": "other@example.com", "password": "password123",
    })
    other_login = client.post("/api/auth/login", json={"email": "other@example.com", "password": "password123"})
    other_headers = {"Authorization": f"Bearer {other_login.get_json()['access_token']}"}

    res = client.get("/api/expenses", headers=other_headers)
    assert res.get_json() == []


def test_update_expense(client, auth_headers, category):
    created = client.post("/api/expenses", headers=auth_headers, json={
        "amount": 10, "category_id": category["id"], "date": "2026-07-01",
    }).get_json()

    res = client.put(f"/api/expenses/{created['id']}", headers=auth_headers, json={"amount": 20})

    assert res.status_code == 200
    assert res.get_json()["amount"] == 20


def test_delete_expense(client, auth_headers, category):
    created = client.post("/api/expenses", headers=auth_headers, json={
        "amount": 10, "category_id": category["id"], "date": "2026-07-01",
    }).get_json()

    res = client.delete(f"/api/expenses/{created['id']}", headers=auth_headers)
    assert res.status_code == 200

    list_res = client.get("/api/expenses", headers=auth_headers)
    assert list_res.get_json() == []


def test_spending_summary_groups_by_category_for_current_month(client, auth_headers, category):
    today = datetime.date.today().isoformat()
    client.post("/api/expenses", headers=auth_headers, json={
        "amount": 10, "category_id": category["id"], "date": today,
    })
    client.post("/api/expenses", headers=auth_headers, json={
        "amount": 15, "category_id": category["id"], "date": today,
    })

    res = client.get("/api/expenses/summary", headers=auth_headers)

    assert res.status_code == 200
    body = res.get_json()
    assert body == [{"category": category["name"], "total": 25.0}]

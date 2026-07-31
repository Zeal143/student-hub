""" The combined dashboard endpoint."""
import datetime


def test_dashboard_requires_auth(client):
    res = client.get("/api/dashboard")
    assert res.status_code == 401


def test_dashboard_shape_with_no_data_yet(client, auth_headers):
    res = client.get("/api/dashboard", headers=auth_headers)

    assert res.status_code == 200
    body = res.get_json()
    assert body["user"]["email"] == "student@example.com"
    assert body["recent_expenses"] == []
    assert body["total_spent_this_month"] == 0
    assert body["has_bin_settings"] is False
    assert body["upcoming_bin_collections"] == []


def test_dashboard_reflects_expenses_budgets_and_bins(client, auth_headers, category, bin_schedule, bin_provider):
    today = datetime.date.today().isoformat()
    client.post("/api/expenses", headers=auth_headers, json={
        "amount": 40, "category_id": category["id"], "date": today,
    })
    client.post("/api/budgets", headers=auth_headers, json={"category_id": category["id"], "monthly_limit": 100})
    client.post("/api/bins/settings", headers=auth_headers, json={
        "eircode": "D02 AF30", "provider_id": bin_provider["id"],
    })

    res = client.get("/api/dashboard", headers=auth_headers)

    body = res.get_json()
    assert body["total_spent_this_month"] == 40
    assert len(body["recent_expenses"]) == 1
    assert len(body["budgets"]) == 1
    assert body["has_bin_settings"] is True
    assert len(body["upcoming_bin_collections"]) == 1 

    budget = body["budgets"][0]
    assert budget["spent"] == 40
    assert budget["remaining"] == 60
    assert budget["over_budget"] is False

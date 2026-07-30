""" monthly category budgets and remaining-budget calculation."""
import datetime


def test_set_budget_creates_a_new_budget(client, auth_headers, category):
    res = client.post("/api/budgets", headers=auth_headers, json={
        "category_id": category["id"], "monthly_limit": 200,
    })
    assert res.status_code == 200
    assert res.get_json()["monthly_limit"] == 200


def test_set_budget_updates_existing_budget_for_same_category(client, auth_headers, category):
    client.post("/api/budgets", headers=auth_headers, json={"category_id": category["id"], "monthly_limit": 200})

    res = client.post("/api/budgets", headers=auth_headers, json={"category_id": category["id"], "monthly_limit": 300})

    assert res.status_code == 200
    list_res = client.get("/api/budgets", headers=auth_headers)
    assert len(list_res.get_json()) == 1  # updated in place, not duplicated
    assert list_res.get_json()[0]["monthly_limit"] == 300


def test_set_budget_rejects_non_positive_limit(client, auth_headers, category):
    res = client.post("/api/budgets", headers=auth_headers, json={"category_id": category["id"], "monthly_limit": 0})
    assert res.status_code == 400


def test_list_budgets_reports_spent_and_remaining(client, auth_headers, category):
    client.post("/api/budgets", headers=auth_headers, json={"category_id": category["id"], "monthly_limit": 100})
    today = datetime.date.today().isoformat()
    client.post("/api/expenses", headers=auth_headers, json={
        "amount": 30, "category_id": category["id"], "date": today,
    })

    res = client.get("/api/budgets", headers=auth_headers)

    assert res.status_code == 200
    budget = res.get_json()[0]
    assert budget["spent"] == 30
    assert budget["remaining"] == 70
    assert budget["over_budget"] is False


def test_list_budgets_flags_over_budget(client, auth_headers, category):
    client.post("/api/budgets", headers=auth_headers, json={"category_id": category["id"], "monthly_limit": 50})
    today = datetime.date.today().isoformat()
    client.post("/api/expenses", headers=auth_headers, json={
        "amount": 75, "category_id": category["id"], "date": today,
    })

    res = client.get("/api/budgets", headers=auth_headers)

    assert res.get_json()[0]["over_budget"] is True


def test_delete_budget(client, auth_headers, category):
    created = client.post("/api/budgets", headers=auth_headers, json={
        "category_id": category["id"], "monthly_limit": 100,
    }).get_json()

    res = client.delete(f"/api/budgets/{created['id']}", headers=auth_headers)

    assert res.status_code == 200
    assert client.get("/api/budgets", headers=auth_headers).get_json() == []

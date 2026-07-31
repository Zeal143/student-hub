"""Savings goals and progress tracking"""


def test_create_goal(client, auth_headers):
    res = client.post("/api/savings", headers=auth_headers, json={
        "name": "Summer trip", "target_amount": 500, "target_date": "2026-08-01",
    })
    assert res.status_code == 201
    body = res.get_json()
    assert body["name"] == "Summer trip"
    assert body["current_amount"] == 0
    assert body["progress_pct"] == 0


def test_create_goal_rejects_missing_name(client, auth_headers):
    res = client.post("/api/savings", headers=auth_headers, json={"name": "", "target_amount": 500})
    assert res.status_code == 400


def test_create_goal_rejects_non_positive_target(client, auth_headers):
    res = client.post("/api/savings", headers=auth_headers, json={"name": "Trip", "target_amount": 0})
    assert res.status_code == 400


def test_update_goal_progress(client, auth_headers):
    goal = client.post("/api/savings", headers=auth_headers, json={
        "name": "Summer trip", "target_amount": 500,
    }).get_json()

    res = client.put(f"/api/savings/{goal['id']}", headers=auth_headers, json={"current_amount": 250})

    assert res.status_code == 200
    body = res.get_json()
    assert body["current_amount"] == 250
    assert body["progress_pct"] == 50.0


def test_delete_goal(client, auth_headers):
    goal = client.post("/api/savings", headers=auth_headers, json={
        "name": "Summer trip", "target_amount": 500,
    }).get_json()

    res = client.delete(f"/api/savings/{goal['id']}", headers=auth_headers)

    assert res.status_code == 200
    assert client.get("/api/savings", headers=auth_headers).get_json() == []

"""Eircode and provider based bin schedule lookup."""


def test_list_providers_is_public(client, bin_provider):
    res = client.get("/api/bins/providers")
    assert res.status_code == 200
    assert res.get_json() == [{"id": bin_provider["id"], "name": bin_provider["name"]}]


def test_set_bin_settings_rejects_invalid_eircode(client, auth_headers, bin_provider):
    res = client.post("/api/bins/settings", headers=auth_headers, json={
        "eircode": "not-a-real-eircode", "provider_id": bin_provider["id"],
    })
    assert res.status_code == 400


def test_set_bin_settings_rejects_unknown_combination(client, auth_headers, bin_provider):
    # Valid-looking Eircode, but no seeded BinSchedule matches this prefix/provider.
    res = client.post("/api/bins/settings", headers=auth_headers, json={
        "eircode": "T12 AB34", "provider_id": bin_provider["id"],
    })
    assert res.status_code == 404


def test_set_bin_settings_succeeds_for_known_combination(client, auth_headers, bin_schedule, bin_provider):
    res = client.post("/api/bins/settings", headers=auth_headers, json={
        "eircode": "D02 AF30", "provider_id": bin_provider["id"],
    })
    assert res.status_code == 200
    assert res.get_json()["eircode"] == "D02 AF30"


def test_get_schedule_requires_settings_to_be_set_first(client, auth_headers):
    res = client.get("/api/bins/schedule", headers=auth_headers)
    assert res.status_code == 400


def test_get_schedule_returns_upcoming_collections(client, auth_headers, bin_schedule, bin_provider):
    client.post("/api/bins/settings", headers=auth_headers, json={
        "eircode": "D02 AF30", "provider_id": bin_provider["id"],
    })

    res = client.get("/api/bins/schedule", headers=auth_headers)

    assert res.status_code == 200
    body = res.get_json()
    assert len(body) == 3  #
    assert body[0]["bin_type"] == "general"
    assert body == sorted(body, key=lambda row: row["collection_date"])

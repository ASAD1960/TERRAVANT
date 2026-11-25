def _farm(client, h, name="Green Acres"):
    r = client.post("/api/v1/farms", json={"farm_name": name, "location": "Sahiwal", "area": 12.5, "area_unit": "acre"}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


def test_farm_field_soil_lifecycle(client, farmer):                                   # TC-06
    farm = _farm(client, farmer)
    f = client.post("/api/v1/fields", json={"farm_id": farm["id"], "field_name": "North", "area": 4, "latitude": 30.66, "longitude": 73.1}, headers=farmer)
    assert f.status_code == 201
    fid = f.json()["id"]
    s = client.post(f"/api/v1/fields/{fid}/soil", json={"nitrogen": 30, "phosphorus": 5, "potassium": 90, "ph": 8.1}, headers=farmer)
    assert s.status_code == 201
    assert len(client.get(f"/api/v1/fields/{fid}/soil", headers=farmer).json()) == 1
    a = client.post(f"/api/v1/fields/{fid}/activities", json={"activity_type": "sowing", "activity_date": "2026-11-10"}, headers=farmer)
    assert a.status_code == 201
    detail = client.get(f"/api/v1/farms/{farm['id']}", headers=farmer).json()
    assert detail["fields"][0]["field_name"] == "North"


def test_ownership_isolation(client, farmer, other):                                  # TC-05
    farm = _farm(client, farmer, "Private")
    assert client.get(f"/api/v1/farms/{farm['id']}", headers=other).status_code == 404
    assert client.put(f"/api/v1/farms/{farm['id']}", json={"farm_name": "Hijack"}, headers=other).status_code == 404
    assert client.delete(f"/api/v1/farms/{farm['id']}", headers=other).status_code == 404
    assert client.post("/api/v1/fields", json={"farm_id": farm["id"], "field_name": "x"}, headers=other).status_code == 404
    assert farm["id"] not in [f["id"] for f in client.get("/api/v1/farms", headers=other).json()]


def test_validation(client, farmer):
    assert client.post("/api/v1/farms", json={"farm_name": "X", "area": -3}, headers=farmer).status_code == 422
    assert client.post("/api/v1/farms", json={"farm_name": "Okay", "area_unit": "parsec"}, headers=farmer).status_code == 422


def test_delete_farm_cascades(client, farmer):
    farm = _farm(client, farmer, "Temp")
    fid = client.post("/api/v1/fields", json={"farm_id": farm["id"], "field_name": "F"}, headers=farmer).json()["id"]
    assert client.delete(f"/api/v1/farms/{farm['id']}", headers=farmer).status_code == 200
    assert client.put(f"/api/v1/fields/{fid}", json={"field_name": "Z"}, headers=farmer).status_code == 404


def test_crops_catalog(client, farmer):
    names = [c["crop_name"] for c in client.get("/api/v1/crops", headers=farmer).json()]
    assert "wheat" in names and "rice" in names


def test_updates_reject_null_required_fields(client, farmer):
    farm = _farm(client, farmer, "Validation Farm")

    response = client.put(
        f"/api/v1/farms/{farm['id']}",
        json={"farm_name": None},
        headers=farmer,
    )
    assert response.status_code == 422

    response = client.put(
        f"/api/v1/farms/{farm['id']}",
        json={"area_unit": None},
        headers=farmer,
    )
    assert response.status_code == 422

    field = client.post(
        "/api/v1/fields",
        json={"farm_id": farm["id"], "field_name": "North"},
        headers=farmer,
    ).json()

    response = client.put(
        f"/api/v1/fields/{field['id']}",
        json={"field_name": None},
        headers=farmer,
    )
    assert response.status_code == 422

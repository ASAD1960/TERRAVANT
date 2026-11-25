from app.integrations import weather as wx

FAKE = {
    "current": {"temperature_2m": 21.5, "relative_humidity_2m": 60, "precipitation": 0, "wind_speed_10m": 8, "time": "2026-11-19T12:00"},
    "daily": {"time": ["2026-11-19", "2026-11-20"], "temperature_2m_max": [24, 43], "temperature_2m_min": [10, 1],
              "precipitation_sum": [0, 30], "precipitation_probability_max": [5, 90]},
}


def test_weather_forecast_and_advisories(client, farmer, monkeypatch):
    monkeypatch.setattr(wx, "_get", lambda url, params: FAKE)
    d = client.get("/api/v1/weather/forecast", headers=farmer).json()
    assert d["current"]["temperature_c"] == 21.5 and len(d["forecast"]) == 2
    text = " ".join(d["advisories"])
    assert "heat" in text and "heavy rain" in text and "frost" in text


def test_weather_provider_down_is_graceful(client, farmer, monkeypatch):           # TC-11
    def boom(url, params):
        raise wx.WeatherUnavailable("down")
    monkeypatch.setattr(wx, "_get", boom)
    r = client.get("/api/v1/weather/current", headers=farmer)
    assert r.status_code == 503 and "unavailable" in r.json()["detail"].lower() or r.status_code == 503
    assert client.get("/health").json() == {"status": "ok"}                          # platform stays up (BR-07)


def test_weather_field_without_coords(client, farmer):
    farm = client.post("/api/v1/farms", json={"farm_name": "NoGeo"}, headers=farmer).json()
    fid = client.post("/api/v1/fields", json={"farm_id": farm["id"], "field_name": "f"}, headers=farmer).json()["id"]
    assert client.get(f"/api/v1/weather/current?field_id={fid}", headers=farmer).status_code == 422


def test_dashboard_and_report(client, farmer):                                      # TC-12
    d = client.get("/api/v1/analytics/dashboard", headers=farmer).json()
    assert d["total_farms"] >= 1 and "prediction_counts" in d
    r = client.get("/api/v1/analytics/reports", headers=farmer)
    assert r.status_code == 200 and r.text.startswith("farm,location")
    assert client.get("/api/v1/analytics/crops", headers=farmer).status_code == 200


def test_notifications_flow(client, farmer):
    client.post("/api/v1/predictions/crop", json={"nitrogen": 80, "phosphorus": 50, "potassium": 40, "temperature": 16, "humidity": 55, "ph": 7.3, "rainfall": 60}, headers=farmer)
    n = client.get("/api/v1/analytics/notifications", headers=farmer).json()
    assert n and not n[0]["is_read"]
    client.post(f"/api/v1/analytics/notifications/{n[0]['id']}/read", headers=farmer)
    assert client.get("/api/v1/analytics/notifications", headers=farmer).json()[0]["is_read"]


def test_admin_rbac_and_audit(client, farmer, other, admin):
    assert client.get("/api/v1/admin/users", headers=farmer).status_code == 403
    assert client.get("/api/v1/admin/audit-logs", headers=farmer).status_code == 403
    users = client.get("/api/v1/admin/users", headers=admin).json()
    target = next(u for u in users if u["email"] == "farmer2@example.com")
    r = client.patch(f"/api/v1/admin/users/{target['id']}/status", json={"status": "suspended"}, headers=admin)
    assert r.status_code == 200
    logs = client.get("/api/v1/admin/audit-logs?action=admin.user_status", headers=admin).json()   # BR-08
    assert logs and logs[0]["details"]["status"] == "suspended"
    client.patch(f"/api/v1/admin/users/{target['id']}/status", json={"status": "active"}, headers=admin)


def test_admin_cannot_suspend_self_and_models_listed(client, admin):
    me = client.get("/api/v1/users/me", headers=admin).json()
    assert client.patch(f"/api/v1/admin/users/{me['id']}/status", json={"status": "suspended"}, headers=admin).status_code == 400
    m = client.get("/api/v1/admin/models", headers=admin).json()
    assert {v["model_name"] for v in m["versions"]} >= {"crop_recommendation", "yield_prediction"}      # BR-05
    assert m["versions"][0]["data_source"]


def test_suspended_user_locked_out(client, admin):
    client.post("/api/v1/auth/register", json={"full_name": "Sus Pended", "email": "sus@example.com", "password": "S3cure-passw0rd"})
    h = {"Authorization": "Bearer " + client.post("/api/v1/auth/login", json={"email": "sus@example.com", "password": "S3cure-passw0rd"}).json()["access_token"]}
    uid = client.get("/api/v1/users/me", headers=h).json()["id"]
    client.patch(f"/api/v1/admin/users/{uid}/status", json={"status": "suspended"}, headers=admin)
    assert client.get("/api/v1/users/me", headers=h).status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": "sus@example.com", "password": "S3cure-passw0rd"}).status_code == 401


def test_ready_and_security_headers(client):
    r = client.get("/ready")
    assert r.status_code == 200 and r.headers["x-content-type-options"] == "nosniff"

def test_weather_rejects_partial_coordinates(client, farmer):
    for params in ("lat=31.5", "lon=74.3"):
        response = client.get(
            f"/api/v1/weather/current?{params}",
            headers=farmer,
        )
        assert response.status_code == 422


def test_dashboard_converts_all_farm_units_to_acres(client, farmer):
    from sqlalchemy import select

    from app.database import SessionLocal
    from app.models import Farm

    user = client.get("/api/v1/users/me", headers=farmer).json()

    farms = [
        {"farm_name": "Unit Test Acre", "area": 1, "area_unit": "acre"},
        {"farm_name": "Unit Test Hectare", "area": 2, "area_unit": "hectare"},
        {"farm_name": "Unit Test Kanal", "area": 4, "area_unit": "kanal"},
        {"farm_name": "Unit Test Marla", "area": 8, "area_unit": "marla"},
    ]

    for payload in farms:
        response = client.post("/api/v1/farms", json=payload, headers=farmer)
        assert response.status_code == 201, response.text

    conversions = {
        "acre": 1,
        "hectare": 2.47105,
        "kanal": 0.125,
        "marla": 0.00625,
    }

    with SessionLocal() as db:
        records = db.scalars(
            select(Farm).where(Farm.owner_id == user["id"])
        ).all()
        expected = round(
            sum(float(f.area or 0) * conversions[f.area_unit] for f in records),
            2,
        )

    dashboard = client.get("/api/v1/analytics/dashboard", headers=farmer)
    assert dashboard.status_code == 200
    assert dashboard.json()["total_area"] == expected
    assert dashboard.json()["area_unit"] == "acre"

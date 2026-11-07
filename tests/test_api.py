from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import make_client


def new_bike(c, **kw):
    body = {"name": "Vario 125", "plate": "B 1234 XY", "type": "scooter", "km": 10000, **kw}
    r = c.post("/api/bikes", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_register_login_logout_me():
    c = make_client()
    assert c.get("/api/me").json()["email"] == "a@example.com"
    assert c.post("/api/logout").status_code == 204
    assert c.get("/api/me").status_code == 401
    assert c.post("/api/login", json={"email": "A@example.com", "password": "correct-horse"}).status_code == 200
    assert c.get("/api/me").status_code == 200


def test_duplicate_email_and_bad_password():
    make_client()
    c = TestClient(app)
    assert c.post("/api/register", json={"email": "a@example.com", "password": "whatever123"}).status_code == 409
    assert c.post("/api/register", json={"email": "b@example.com", "password": "short"}).status_code == 422
    assert c.post("/api/login", json={"email": "a@example.com", "password": "wrong-pass"}).status_code == 401


def test_login_rate_limit():
    make_client()
    c = TestClient(app)
    for _ in range(5):
        assert c.post("/api/login", json={"email": "a@example.com", "password": "wrong-pass"}).status_code == 401
    # even the right password is refused while locked
    assert c.post("/api/login", json={"email": "a@example.com", "password": "correct-horse"}).status_code == 429


def test_create_bike_seeds_tasks_by_type(client):
    scooter = new_bike(client)
    parts = {t["part"] for t in scooter["tasks"]}
    assert {"engine_oil", "cvt_belt", "gear_oil"} <= parts and "chain" not in parts
    assert all(t["state"] == "due" for t in scooter["tasks"])
    sport = new_bike(client, type="sport")
    assert "chain" in {t["part"] for t in sport["tasks"]}
    assert scooter["current_km"] == 10000


def test_log_service_updates_status_and_undo(client):
    bike = new_bike(client)
    oil = next(t for t in bike["tasks"] if t["part"] == "engine_oil")
    r = client.post(f"/api/bikes/{bike['id']}/logs",
                    json={"task_ids": [oil["id"]], "date": str(date.today()), "km": 10500, "cost": "85000"})
    assert r.status_code == 201
    view = r.json()
    oil2 = next(t for t in view["tasks"] if t["id"] == oil["id"])
    assert oil2["state"] == "ok" and oil2["km_left"] == 3000 and view["current_km"] == 10500
    # km tracker pushes it into "soon"
    view = client.post(f"/api/bikes/{bike['id']}/odometer", json={"km": 13300}).json()
    assert next(t for t in view["tasks"] if t["id"] == oil["id"])["state"] == "soon"
    # undo
    for lid in r.json()["created_log_ids"]:
        assert client.delete(f"/api/bikes/{bike['id']}/logs/{lid}").status_code == 204
    view = client.get(f"/api/bikes/{bike['id']}").json()
    assert next(t for t in view["tasks"] if t["id"] == oil["id"])["state"] == "due"


def test_overdue_by_date(client):
    bike = new_bike(client)
    gen = next(t for t in bike["tasks"] if t["part"] == "general")  # every 30 days
    old = date.today() - timedelta(days=40)
    view = client.post(f"/api/bikes/{bike['id']}/logs",
                       json={"task_ids": [gen["id"]], "date": str(old), "km": 9000}).json()
    assert next(t for t in view["tasks"] if t["id"] == gen["id"])["state"] == "overdue"
    assert view["worst"] == "overdue" and view["tasks"][0]["state"] == "overdue"


def test_task_crud(client):
    bike = new_bike(client)
    bid = bike["id"]
    assert client.post(f"/api/bikes/{bid}/tasks", json={"part": "general", "name": "Wash"}).status_code == 422
    view = client.post(f"/api/bikes/{bid}/tasks", json={"part": "general", "name": "Wash", "every_days": 7}).json()
    wash = next(t for t in view["tasks"] if t["name"] == "Wash")
    view = client.patch(f"/api/bikes/{bid}/tasks/{wash['id']}", json={"every_km": 500}).json()
    assert next(t for t in view["tasks"] if t["id"] == wash["id"])["every_km"] == 500
    assert client.patch(f"/api/bikes/{bid}/tasks/{wash['id']}",
                        json={"every_km": None, "every_days": None}).status_code == 422
    assert client.delete(f"/api/bikes/{bid}/tasks/{wash['id']}").status_code == 204


def test_other_user_cannot_touch_bike(client):
    bike = new_bike(client)
    bid = bike["id"]
    tid = bike["tasks"][0]["id"]
    other = make_client("b@example.com")
    assert other.get(f"/api/bikes/{bid}").status_code == 404
    assert other.patch(f"/api/bikes/{bid}", json={"name": "mine"}).status_code == 404
    assert other.delete(f"/api/bikes/{bid}").status_code == 404
    assert other.post(f"/api/bikes/{bid}/odometer", json={"km": 1}).status_code == 404
    assert other.post(f"/api/bikes/{bid}/logs",
                      json={"task_ids": [tid], "date": str(date.today()), "km": 1}).status_code == 404
    assert other.get("/api/bikes").json() == []
    # can't attach someone else's task to your own bike either
    mine = new_bike(other)
    assert other.post(f"/api/bikes/{mine['id']}/logs",
                      json={"task_ids": [tid], "date": str(date.today()), "km": 1}).status_code == 404


def test_delete_bike_and_export(client):
    bike = new_bike(client)
    new_bike(client, name="CB150R", type="sport")
    exp = client.get("/api/export").json()
    assert len(exp["bikes"]) == 2
    assert client.delete(f"/api/bikes/{bike['id']}").status_code == 204
    assert len(client.get("/api/bikes").json()) == 1

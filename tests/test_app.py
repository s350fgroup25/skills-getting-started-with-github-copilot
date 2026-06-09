import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


@pytest.fixture
def client():
    return TestClient(app)


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_list(client):
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert data["Chess Club"]["description"].startswith("Learn strategies")
    assert data["Chess Club"]["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]


def test_signup_for_activity_adds_participant(client):
    email = "student1@mergington.edu"
    activity = quote("Chess Club", safe="")

    response = client.post(f"/activities/{activity}/signup?email={quote(email, safe='')}" )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in activities["Chess Club"]["participants"]


def test_duplicate_signup_returns_400(client):
    email = "student2@mergington.edu"
    activity = quote("Chess Club", safe="")

    response1 = client.post(f"/activities/{activity}/signup?email={quote(email, safe='')}" )
    assert response1.status_code == 200

    response2 = client.post(f"/activities/{activity}/signup?email={quote(email, safe='')}" )
    assert response2.status_code == 400
    assert response2.json()["detail"] == "Student already signed up for this activity"


def test_unregister_participant_removes_participant(client):
    activity = quote("Chess Club", safe="")
    email = "michael@mergington.edu"

    response = client.delete(f"/activities/{activity}/unregister?email={quote(email, safe='')}" )

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_missing_participant_returns_404(client):
    activity = quote("Chess Club", safe="")
    email = "missing@mergington.edu"

    response = client.delete(f"/activities/{activity}/unregister?email={quote(email, safe='')}" )

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in the activity"


def test_signup_for_unknown_activity_returns_404(client):
    activity = quote("Unknown Activity", safe="")
    email = "student3@mergington.edu"

    response = client.post(f"/activities/{activity}/signup?email={quote(email, safe='')}" )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_for_unknown_activity_returns_404(client):
    activity = quote("Unknown Activity", safe="")
    email = "student4@mergington.edu"

    response = client.delete(f"/activities/{activity}/unregister?email={quote(email, safe='')}" )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"

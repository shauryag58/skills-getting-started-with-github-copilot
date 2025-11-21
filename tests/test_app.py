from fastapi.testclient import TestClient
import copy
import urllib.parse

from src.app import app, activities

import pytest


@pytest.fixture(autouse=True)
def client_and_restore():
    """Provide a TestClient and restore the in-memory activities after each test."""
    original = copy.deepcopy(activities)
    client = TestClient(app)
    try:
        yield client
    finally:
        # Restore the original activities to avoid test cross-talk
        activities.clear()
        activities.update(original)


def test_get_activities(client_and_restore):
    client = client_and_restore
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_and_unregister_flow(client_and_restore):
    client = client_and_restore
    activity = "Chess Club"
    email = "tester+signup@example.com"

    # Ensure email not already in participants
    assert email not in activities[activity]["participants"]

    # Signup
    signup_url = f"/activities/{urllib.parse.quote(activity)}/signup?email={urllib.parse.quote(email)}"
    resp = client.post(signup_url)
    assert resp.status_code == 200
    assert "Signed up" in resp.json().get("message", "")

    # Verify participant present
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert email in data[activity]["participants"]

    # Signing up again should fail (400)
    resp = client.post(signup_url)
    assert resp.status_code == 400

    # Now unregister
    unregister_url = f"/activities/{urllib.parse.quote(activity)}/unregister?email={urllib.parse.quote(email)}"
    resp = client.delete(unregister_url)
    assert resp.status_code == 200
    assert "Unregistered" in resp.json().get("message", "")

    # Verify removal
    resp = client.get("/activities")
    data = resp.json()
    assert email not in data[activity]["participants"]


def test_unregister_nonexistent_participant_returns_404(client_and_restore):
    client = client_and_restore
    activity = "Programming Class"
    email = "nonexistent@example.com"

    unregister_url = f"/activities/{urllib.parse.quote(activity)}/unregister?email={urllib.parse.quote(email)}"
    resp = client.delete(unregister_url)
    assert resp.status_code == 404
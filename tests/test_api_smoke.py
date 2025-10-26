"""
Smoke tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from engine_reference import app

client = TestClient(app)


def test_next_question_endpoint():
    """Test /questionnaire/next endpoint."""
    response = client.post(
        "/questionnaire/next",
        json={"session_id": "test-session-1", "context": {"role": "support"}},
    )

    assert response.status_code == 200
    data = response.json()
    assert "question" in data
    assert "id" in data["question"]
    assert "answer_key" not in data["question"]


def test_submit_answer_endpoint():
    """Test /questionnaire/submit endpoint."""
    # First get a question
    next_response = client.post(
        "/questionnaire/next", json={"session_id": "test-session-2"}
    )
    question = next_response.json()["question"]

    # Submit an answer
    response = client.post(
        "/questionnaire/submit",
        json={
            "session_id": "test-session-2",
            "question_id": question["id"],
            "selected": "A",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "correct" in data
    assert "score" in data
    assert "feedback" in data
    assert "rationale" in data


def test_submit_invalid_question():
    """Test submitting answer for non-existent question."""
    response = client.post(
        "/questionnaire/submit",
        json={"session_id": "test-session-3", "question_id": 99999, "selected": "A"},
    )

    assert response.status_code == 404


@pytest.mark.skipif(
    not pytest.importorskip("tss_crypto").SECRETSHARING_AVAILABLE,
    reason="secretsharing library not installed",
)
def test_tss_event_endpoint():
    """Test /tss/event endpoint."""
    response = client.post(
        "/tss/event",
        json={
            "org_id": "test-org",
            "event_type": "test-event",
            "payload": {"key": "value"},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "payload_id" in data
    assert "shares_demo" in data


@pytest.mark.skipif(
    not pytest.importorskip("tss_crypto").SECRETSHARING_AVAILABLE,
    reason="secretsharing library not installed",
)
def test_tss_reconstruct_endpoint():
    """Test /tss/reconstruct endpoint."""
    # First create an event
    create_response = client.post(
        "/tss/event",
        json={
            "org_id": "test-org",
            "event_type": "test-event",
            "payload": {"key": "value"},
        },
    )

    create_data = create_response.json()
    payload_id = create_data["payload_id"]
    shares = create_data["shares_demo"]

    # Pick two shares
    roles = list(shares.keys())[:2]
    provided_roles = {role: shares[role] for role in roles}

    # Reconstruct
    response = client.post(
        "/tss/reconstruct",
        json={
            "payload_id": payload_id,
            "provided_roles": provided_roles,
            "reason": "test reconstruction",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "payload_hash" in data
    assert "data" in data
    assert data["data"]["payload"] == {"key": "value"}


def test_tss_reconstruct_insufficient_shares():
    """Test TSS reconstruction with insufficient shares."""
    # First create an event
    create_response = client.post(
        "/tss/event",
        json={
            "org_id": "test-org",
            "event_type": "test-event",
            "payload": {"key": "value"},
        },
    )

    if create_response.status_code != 200:
        pytest.skip("TSS not available")

    create_data = create_response.json()
    payload_id = create_data["payload_id"]
    shares = create_data["shares_demo"]

    # Try with only one share
    roles = list(shares.keys())[:1]
    provided_roles = {role: shares[role] for role in roles}

    response = client.post(
        "/tss/reconstruct",
        json={
            "payload_id": payload_id,
            "provided_roles": provided_roles,
            "reason": "test reconstruction",
        },
    )

    assert response.status_code == 403

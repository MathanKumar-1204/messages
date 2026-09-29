import pytest
import os
import json
from processor import process_jsonl_stream, process_jsonl_file
from app import app


def test_sample_messages_requirement():
    """
    Test 1: Required sample containing:
    Line 1: D01 sequence 1 ok
    Line 2: D01 sequence 1 ok (duplicate)
    Line 3: D02 sequence 2 error
    Line 4: malformed line
    Line 5: D01 sequence 3 error
    """
    sample_lines = [
        '{"device_id": "D01", "sequence": 1, "status": "ok"}\n',
        '{"device_id": "D01", "sequence": 1, "status": "ok"}\n',
        '{"device_id": "D02", "sequence": 2, "status": "error"}\n',
        '{bad json\n',
        '{"device_id": "D01", "sequence": 3, "status": "error"}\n',
    ]

    result = process_jsonl_stream(sample_lines)

    assert result["totals"]["accepted"] == 3
    assert result["totals"]["duplicates"] == 1
    assert result["totals"]["errors"] == 1

    assert result["errors"] == [{"line": 4, "error": "BAD_JSON"}]

    devices = result["devices"]
    assert "D01" in devices
    assert "D02" in devices

    assert devices["D01"] == {
        "ok": 1,
        "error": 1,
        "last_sequence": 3,
        "last_status": "error",
    }

    assert devices["D02"] == {
        "ok": 0,
        "error": 1,
        "last_sequence": 2,
        "last_status": "error",
    }


def test_later_arriving_lower_sequence():
    """
    Test 2: Required test for a later-arriving lower sequence.
    Sequence 5 (error) arrives first, then sequence 3 (ok) arrives later.
    last_sequence must remain 5 and last_status must remain 'error',
    while ok and error counts accumulate correctly.
    """
    lines = [
        '{"device_id": "D01", "sequence": 5, "status": "error"}\n',
        '{"device_id": "D01", "sequence": 3, "status": "ok"}\n',
    ]

    result = process_jsonl_stream(lines)

    assert result["totals"]["accepted"] == 2
    assert result["totals"]["duplicates"] == 0
    assert result["totals"]["errors"] == 0

    d01 = result["devices"]["D01"]
    assert d01["ok"] == 1
    assert d01["error"] == 1
    assert d01["last_sequence"] == 5
    assert d01["last_status"] == "error"


def test_empty_input():
    """
    Test 3: Required test for empty input.
    Must return zero totals, empty devices dict, and empty errors list.
    """
    result = process_jsonl_stream([])

    assert result["totals"]["accepted"] == 0
    assert result["totals"]["duplicates"] == 0
    assert result["totals"]["errors"] == 0
    assert result["devices"] == {}
    assert result["errors"] == []


def test_invalid_records():
    """
    Additional validation test: ensures schema validation errors produce INVALID_RECORD.
    """
    lines = [
        '{"device_id": "", "sequence": 1, "status": "ok"}\n',           # Empty device_id
        '{"device_id": "   ", "sequence": 1, "status": "ok"}\n',        # Whitespace device_id
        '{"device_id": "D01", "sequence": true, "status": "ok"}\n',     # Boolean sequence
        '{"device_id": "D01", "sequence": -1, "status": "ok"}\n',       # Negative sequence
        '{"device_id": "D01", "sequence": 1, "status": "unknown"}\n',  # Invalid status
        '{"device_id": "D01", "sequence": 1, "status": "ok", "extra": 1}\n', # Extra key
    ]

    result = process_jsonl_stream(lines)

    assert result["totals"]["accepted"] == 0
    assert result["totals"]["duplicates"] == 0
    assert result["totals"]["errors"] == 6
    assert all(err["error"] == "INVALID_RECORD" for err in result["errors"])


def test_flask_endpoint_success(tmp_path):
    """
    Tests GET /summary endpoint success case.
    """
    sample_file = tmp_path / "sample.jsonl"
    sample_file.write_text('{"device_id": "D01", "sequence": 1, "status": "ok"}\n')

    with app.test_client() as client:
        import app as app_module
        app_module.SAMPLE_FILE_PATH = str(sample_file)

        response = client.get("/summary")
        assert response.status_code == 200
        data = response.get_json()
        assert data["totals"]["accepted"] == 1
        assert "D01" in data["devices"]


def test_flask_endpoint_file_not_found():
    """
    Tests GET /summary endpoint when sample file is missing.
    Must return a 404 HTTP status code with error details.
    """
    with app.test_client() as client:
        import app as app_module
        app_module.SAMPLE_FILE_PATH = "non_existent_file_xyz.jsonl"

        response = client.get("/summary")
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data
        assert "not found" in data["error"].lower()


def test_flask_index_frontend():
    """
    Tests GET / root route serving HTML dashboard.
    """
    with app.test_client() as client:
        response = client.get("/")
        assert response.status_code == 200
        assert b"Device Message Summary" in response.data
        assert b"<!DOCTYPE html>" in response.data

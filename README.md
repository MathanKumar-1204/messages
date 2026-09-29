# Device Message Summary Service

A Python solution that processes simulated device messages from a JSON Lines (`.jsonl`) file, generates aggregate statistics and per-device summaries, and exposes a `GET /summary` HTTP endpoint built with Flask.

## Quick Start

### 1. Requirements & Setup
- Python 3.8+
- Install dependencies:
  ```bash
  pip install flask pytest
  ```

### 2. Run the HTTP Endpoint
To launch the API server on `http://127.0.0.1:5000`:
```bash
python app.py
```

Query the summary endpoint:
```bash
curl http://127.0.0.1:5000/summary
```

### 3. Run Automated Tests
Run the pytest test suite covering sample data, out-of-order sequence handling, empty input, and invalid records:
```bash
python -m pytest -v
```

---

## React Integration Guide (Fetch & State Management)

*How a React frontend page can consume `GET /summary` and distinguish loading, empty data, and API failures:*

* Use three distinct state variables (`data`, `isLoading`, `error`) initialized as `null`, `true`, and `null` respectively using `useState`.
* Set `isLoading(true)` and reset `error(null)` when initiating `fetch('/summary')`, updating `isLoading(false)` in a `finally` block to display/hide a loading spinner.
* Handle API & network failures by checking `!response.ok` (e.g. HTTP 404/500 error responses from the backend) or catching network exceptions, setting the `error` state with the returned JSON error details (e.g., `data.error`).
* Detect empty data when the request succeeds (`response.ok`) but `data.totals.accepted === 0` and `Object.keys(data.devices).length === 0`, displaying a dedicated empty state UI (e.g., "No device messages processed").
* Render the summary dashboard only when `!isLoading && !error && data`, displaying overall totals (`accepted`, `duplicates`, `errors`) and mapping over `Object.entries(data.devices)` for per-device status metrics.

# Device Message Summary Service

A small Python service that reads simulated device messages from a JSON Lines (`.jsonl`) file, validates and summarizes them, and exposes the summary through a lightweight HTTP API.

## Features

- Processes JSONL input line by line.
- Validates `device_id`, `sequence`, and `status`.
- Continues processing when individual lines contain malformed JSON or invalid records.
- Detects duplicate `(device_id, sequence)` records after validation.
- Tracks `ok` and `error` counts for each device.
- Determines the latest accepted message using the highest sequence number, regardless of input order.
- Exposes the summary through `GET /summary`.
- Includes automated tests for the required cases and API behavior.

## Project Structure

```text
messages/
├── app.py
├── processor.py
├── sample_messages.jsonl
├── test_summary.py
├── templates/
│   └── index.html
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.8+
- `pip`

## Setup

Create and activate a virtual environment if desired:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the Application

Start the Flask application:

```bash
python app.py
```

The service will run locally on:

```text
http://localhost:5000
```

Open the summary endpoint:

```text
http://localhost:5000/summary
```

Or use:

```bash
curl http://localhost:5000/summary
```

## Input Format

Each line in `sample_messages.jsonl` is expected to contain one JSON object with exactly these fields:

```json
{
  "device_id": "D01",
  "sequence": 1,
  "status": "ok"
}
```

Rules:

- `device_id` must be a non-empty, non-whitespace string.
- `sequence` must be an integer greater than or equal to `0`.
- Boolean values are not accepted as `sequence`.
- `status` must be either `ok` or `error`.
- Malformed JSON produces a `BAD_JSON` error.
- A structurally invalid record produces an `INVALID_RECORD` error.
- Processing continues after malformed or invalid lines.

## Duplicate Handling

Duplicate detection is performed only after a record passes validation.

A record is considered a duplicate when the same `(device_id, sequence)` pair has already been accepted.

For example:

```text
D01, sequence 1 -> accepted
D01, sequence 1 -> duplicate
```

The first valid occurrence is accepted, while later occurrences are counted as duplicates even if their status is different.

## Latest Sequence Handling

The latest status for a device is determined by the highest accepted sequence number, not by the order in which records appear in the file.

For example:

```text
D01, sequence 5, error
D01, sequence 3, ok
```

The final device summary remains:

```json
{
  "last_sequence": 5,
  "last_status": "error"
}
```

The later-arriving lower sequence does not replace the higher sequence.

## Sample Result

The provided sample contains:

- `D01` sequence `1`, status `ok`
- The same `D01` sequence `1` record again
- `D02` sequence `2`, status `error`
- One malformed JSON line
- `D01` sequence `3`, status `error`

The expected totals are:

```json
{
  "accepted": 3,
  "duplicates": 1,
  "errors_count": 1
}
```

The device summaries are:

```text
D01 -> ok: 1, error: 1, last_sequence: 3, last_status: error
D02 -> ok: 0, error: 1, last_sequence: 2, last_status: error
```

## API

### `GET /summary`

Returns the processed summary as JSON.

A successful response contains:

```json
{
  "accepted": 3,
  "duplicates": 1,
  "errors_count": 1,
  "errors": [],
  "devices": {}
}
```

The actual `errors` and `devices` values depend on the input file.

If the configured sample file cannot be found, the service returns an error response instead of incorrectly treating the file as empty.

## Testing

Run all automated tests:

```bash
pytest -v
```

The test suite covers:

1. The required sample input and expected summary.
2. A lower sequence arriving after a higher sequence.
3. Empty input.
4. Invalid records.
5. Successful `/summary` API behavior.
6. Missing sample-file behavior.
7. The basic application page.

## React Integration Note

A React page can consume the service without changing the backend:

- Fetch `/summary` when the page loads and store the returned JSON in component state.
- Show a loading state while the request is in progress.
- If the response contains no device data, show an empty-data state instead of rendering an empty dashboard.
- If the request fails or returns an HTTP error, show an API-failure state with a retry option.
- When data is available, render the totals, device summaries, and processing errors from the JSON response.

No React application is required for this assignment.

## Design Choice

The core processing logic is separated from the Flask application.

`processor.py` is responsible for:

- Reading and validating records.
- Detecting duplicates.
- Maintaining per-device state.
- Calculating the latest sequence.
- Producing the final summary.

`app.py` is responsible for:

- Creating the Flask application.
- Serving the API endpoint.
- Handling file and unexpected errors.

This separation keeps the processing logic testable without requiring an HTTP request for every test.

## Assumptions

- The input file is UTF-8 JSON Lines data.
- Each physical line represents one independent message.
- Blank lines are treated as malformed JSON and reported as `BAD_JSON`.
- Device summaries are sorted by `device_id`.
- Only accepted records affect device counts and latest-sequence state.
- Duplicate checking occurs after record validation.

## Time Spent

Approximately 2 hours.

## Known Limitation

The service processes the configured JSONL file for the `/summary` request rather than maintaining persistent state between requests. There is no database or persistent message store, which is intentional for the scope of this assignment.

## Unfinished Work

No major unfinished functionality remains for the requested assignment scope.

A production version could add persistent storage, structured logging, authentication, and more extensive API-level validation, but these are outside the requirements of this exercise.

## AI / Reuse Note

AI tools were used during development for assistance with implementation ideas, validation logic, testing, documentation, and debugging.

The final solution was reviewed and adapted to match the assignment requirements and expected behavior.

## Reproducibility

To run the project from a fresh environment:

```bash
git clone <repository-url>
cd messages
pip install -r requirements.txt
pytest -v
python app.py
```

Then open:

```text
http://localhost:5000/summary
```

## Submission

GitHub repository:

https://github.com/MathanKumar-1204/messages

Live application:

https://messages-xi-wine.vercel.app/

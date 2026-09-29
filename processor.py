import json
from typing import Dict, Any, List, Union


def validate_record(data: Any) -> bool:
    """
    Validates a parsed JSON record against schema requirements:
    - Must be a JSON object (dict) with exactly keys: device_id, sequence, status.
    - device_id must be a non-empty string, excluding whitespace-only strings.
    - sequence must be an integer >= 0, not a boolean.
    - status must be 'ok' or 'error'.
    """
    if not isinstance(data, dict):
        return False
    
    if set(data.keys()) != {"device_id", "sequence", "status"}:
        return False
    
    device_id = data["device_id"]
    if not isinstance(device_id, str) or len(device_id.strip()) == 0:
        return False
    
    sequence = data["sequence"]
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        return False
    
    status = data["status"]
    if status not in ("ok", "error"):
        return False
    
    return True


def process_jsonl_stream(lines: Union[List[str], Any]) -> Dict[str, Any]:
    """
    Processes simulated device messages line-by-line.
    Returns summary dict containing accepted, duplicate, error counts, error list, and device stats.
    """
    accepted = 0
    duplicates = 0
    errors: List[Dict[str, Any]] = []
    seen_pairs = set()
    devices_data: Dict[str, Dict[str, Any]] = {}

    for line_idx, line in enumerate(lines, start=1):
        raw_line = line.strip() if isinstance(line, str) else ""
        if not raw_line:
            errors.append({"line": line_idx, "error": "BAD_JSON"})
            continue
        
        try:
            data = json.loads(raw_line)
        except (json.JSONDecodeError, ValueError):
            errors.append({"line": line_idx, "error": "BAD_JSON"})
            continue
        
        if not validate_record(data):
            errors.append({"line": line_idx, "error": "INVALID_RECORD"})
            continue
        
        device_id = data["device_id"]
        sequence = data["sequence"]
        status = data["status"]
        
        pair = (device_id, sequence)
        if pair in seen_pairs:
            duplicates += 1
            continue
        
        seen_pairs.add(pair)
        accepted += 1
        
        if device_id not in devices_data:
            devices_data[device_id] = {
                "ok": 0,
                "error": 0,
                "last_sequence": sequence,
                "last_status": status,
            }
            if status == "ok":
                devices_data[device_id]["ok"] += 1
            else:
                devices_data[device_id]["error"] += 1
        else:
            dev = devices_data[device_id]
            if status == "ok":
                dev["ok"] += 1
            else:
                dev["error"] += 1
            
            if sequence > dev["last_sequence"]:
                dev["last_sequence"] = sequence
                dev["last_status"] = status

    sorted_devices = {k: devices_data[k] for k in sorted(devices_data.keys())}

    return {
        "totals": {
            "accepted": accepted,
            "duplicates": duplicates,
            "errors": len(errors),
        },
        "accepted": accepted,
        "duplicates": duplicates,
        "errors_count": len(errors),
        "errors": errors,
        "devices": sorted_devices,
    }


def process_jsonl_file(filepath: str) -> Dict[str, Any]:
    """
    Reads a JSON Lines file from disk and returns its summary.
    Raises FileNotFoundError or OSError if file cannot be read.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return process_jsonl_stream(f)

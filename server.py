#!/usr/bin/env python3
import json
import os
from datetime import datetime
from urllib.parse import urlparse

def compare_api_structures(file_paths, output_dir="./dashboard_data", comparison_level="comprehensive"):
    """Compare API structures from multiple files"""
    # Initialize results
    comparison_result = {
        "summary": {
            "total_endpoints": 0,
            "endpoints_with_changes": 0,
            "comparison_time": datetime.now().isoformat()
        },
        "detailed_results": {}
    }
    
    # Process each file's data
    all_endpoints = {}
    for file_data in file_paths:
        data = file_data["data"]
        file_label = file_data["file_label"]
        
        # Extract endpoints from the data
        endpoints = {}
        if isinstance(data, list):
            for entry in data:
                process_entry(entry, endpoints)
        elif isinstance(data, dict):
            if "entries" in data:
                for entry in data["entries"]:
                    process_entry(entry, endpoints)
            else:
                process_entry(data, endpoints)
        
        # Add to all_endpoints with file label
        for key, endpoint in endpoints.items():
            if key not in all_endpoints:
                all_endpoints[key] = {
                    "method": endpoint["method"],
                    "host": endpoint["host"],
                    "path": endpoint["path"],
                    "present_in": [file_label],
                    "missing_in": [],
                    "instances": {file_label: endpoint},
                    "has_changes": False,
                    "differences": {}
                }
            else:
                all_endpoints[key]["present_in"].append(file_label)
                all_endpoints[key]["instances"][file_label] = endpoint
    
    # Compare endpoints
    for key, endpoint in all_endpoints.items():
        # Calculate missing_in
        endpoint["missing_in"] = [f["file_label"] for f in file_paths if f["file_label"] not in endpoint["present_in"]]
        
        # Compare instances if present in multiple files
        if len(endpoint["present_in"]) > 1:
            differences = compare_endpoint_instances(endpoint["instances"], comparison_level)
            if differences:
                endpoint["has_changes"] = True
                endpoint["differences"] = differences
                comparison_result["summary"]["endpoints_with_changes"] += 1
    
    # Update summary
    comparison_result["summary"]["total_endpoints"] = len(all_endpoints)
    comparison_result["detailed_results"] = all_endpoints
    
    return comparison_result

def process_entry(entry, endpoints):
    """Process a single entry and add it to endpoints"""
    if not isinstance(entry, dict):
        return
    
    # Extract method and path
    method = entry.get("method", entry.get("request", {}).get("method", ""))
    path = entry.get("path", "")
    if not path and "url" in entry:
        # Extract path from URL if needed
        parsed_url = urlparse(entry["url"])
        path = parsed_url.path
        if parsed_url.query:
            path += "?" + parsed_url.query
    
    # Extract host
    host = entry.get("host", "")
    if not host and "url" in entry:
        parsed_url = urlparse(entry["url"])
        host = parsed_url.netloc
    
    # Create unique key
    key = f"{method}:{path}"
    
    # Extract response body
    response_body = entry.get("response_body", entry.get("response", {}).get("body", ""))
    if isinstance(response_body, dict):
        response_body = json.dumps(response_body)
    elif not isinstance(response_body, str):
        response_body = str(response_body)
    
    # Create endpoint entry
    endpoint_data = {
        "method": method,
        "host": host,
        "path": path,
        "status": entry.get("status", entry.get("response", {}).get("status", 0)),
        "duration": entry.get("duration", 0),
        "request_headers": entry.get("request_headers", entry.get("request", {}).get("headers", {})),
        "response_headers": entry.get("response_headers", entry.get("response", {}).get("headers", {})),
        "response_body": response_body,
        "url": entry.get("url", "")
    }
    
    endpoints[key] = endpoint_data

def compare_endpoint_instances(instances, comparison_level):
    """Compare different instances of the same endpoint"""
    differences = {
        "status_codes": {},
        "headers": {},
        "response": {},
        "request": {},
        "parameters": {}
    }
    
    instance_labels = list(instances.keys())
    if len(instance_labels) < 2:
        return {}
    
    # Compare first instance with others
    base_label = instance_labels[0]
    base_instance = instances[base_label]
    
    for other_label in instance_labels[1:]:
        other_instance = instances[other_label]
        
        # Compare status codes
        if base_instance["status"] != other_instance["status"]:
            differences["status_codes"] = {
                "type": "value_mismatch",
                base_label: base_instance["status"],
                other_label: other_instance["status"]
            }
        
        # Compare headers if detailed comparison
        if comparison_level in ["detailed", "comprehensive"]:
            header_diffs = compare_headers(
                base_instance["request_headers"],
                other_instance["request_headers"],
                base_label,
                other_label
            )
            if header_diffs:
                differences["headers"].update(header_diffs)
        
        # Compare response bodies if comprehensive comparison
        if comparison_level == "comprehensive":
            try:
                base_body = json.loads(base_instance["response_body"]) if isinstance(base_instance["response_body"], str) else base_instance["response_body"]
                other_body = json.loads(other_instance["response_body"]) if isinstance(other_instance["response_body"], str) else other_instance["response_body"]
                
                body_diffs = compare_json_values(base_body, other_body, base_label, other_label)
                if body_diffs:
                    differences["response"] = body_diffs
            except (json.JSONDecodeError, TypeError):
                # If not JSON, compare as strings
                if base_instance["response_body"] != other_instance["response_body"]:
                    differences["response"] = {
                        "type": "value_mismatch",
                        base_label: base_instance["response_body"],
                        other_label: other_instance["response_body"]
                    }
    
    # Remove empty difference categories
    return {k: v for k, v in differences.items() if v}

def compare_headers(headers1, headers2, label1, label2):
    """Compare two sets of headers"""
    differences = {}
    
    # Compare headers present in both
    all_headers = set(headers1.keys()) | set(headers2.keys())
    for header in all_headers:
        value1 = headers1.get(header, "")
        value2 = headers2.get(header, "")
        
        if value1 != value2:
            differences[header] = {
                "type": "value_mismatch",
                label1: value1,
                label2: value2
            }
    
    return differences

def compare_json_values(value1, value2, label1, label2):
    """Compare two JSON values recursively"""
    if type(value1) != type(value2):
        return {
            "type": "value_mismatch",
            label1: value1,
            label2: value2
        }
    
    if isinstance(value1, dict):
        differences = {}
        all_keys = set(value1.keys()) | set(value2.keys())
        
        for key in all_keys:
            if key not in value1:
                differences[key] = {
                    "type": "value_mismatch",
                    label1: None,
                    label2: value2[key]
                }
            elif key not in value2:
                differences[key] = {
                    "type": "value_mismatch",
                    label1: value1[key],
                    label2: None
                }
            else:
                nested_diff = compare_json_values(value1[key], value2[key], label1, label2)
                if nested_diff:
                    differences[key] = nested_diff
        
        return differences if differences else None
    
    elif isinstance(value1, list):
        if len(value1) != len(value2):
            return {
                "type": "value_mismatch",
                label1: value1,
                label2: value2
            }
        
        differences = {}
        for i, (item1, item2) in enumerate(zip(value1, value2)):
            nested_diff = compare_json_values(item1, item2, label1, label2)
            if nested_diff:
                differences[str(i)] = nested_diff
        
        return differences if differences else None
    
    elif value1 != value2:
        return {
            "type": "value_mismatch",
            label1: value1,
            label2: value2
        }
    
    return None 
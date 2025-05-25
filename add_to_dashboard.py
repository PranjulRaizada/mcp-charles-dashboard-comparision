#!/usr/bin/env python3
import sys
import json
import os
from datetime import datetime
import argparse

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Add existing comparison file to dashboard")
    parser.add_argument('--comparison_file', type=str, required=True, 
                        help='Path to existing comparison file')
    parser.add_argument('--output_dir', type=str, default="./dashboard_data",
                        help='Directory where dashboard files are stored')
    parser.add_argument('--metadata', type=str, default="{}",
                        help='JSON string of metadata to include')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Parse metadata if provided
    try:
        metadata = json.loads(args.metadata)
    except json.JSONDecodeError:
        print("Error: metadata is not valid JSON")
        sys.exit(1)
    
    # Read the comparison file
    try:
        with open(args.comparison_file, 'r') as f:
            comparison_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading comparison file: {e}")
        sys.exit(1)
        
    # Extract file labels from the comparison data
    file_labels = comparison_data.get("files_compared", [])
    if not file_labels:
        file_labels = [os.path.basename(f).split('.')[0] for f in metadata.get("version_labels", ["version1", "version2"])]
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # Process the comparison data for dashboard
    dashboard_data = {
        "metadata": {
            "comparison_time": comparison_data.get("comparison_time", datetime.now().isoformat()),
            "file_labels": file_labels,
            "custom_metadata": metadata,
            "total_endpoints": comparison_data.get("total_endpoints_analyzed", 0),
            "endpoints_with_changes": comparison_data.get("endpoints_with_changes", 0)
        },
        "endpoints": {},
        "summary": {
            "by_host": {},
            "by_change_type": {
                "added": [],
                "removed": [],
                "modified": []
            }
        }
    }
    
    # Process detailed results
    detailed_results = comparison_data.get("detailed_results", {})
    for endpoint_key, endpoint_data in detailed_results.items():
        # Dashboard-friendly endpoint format
        endpoint_summary = {
            "method": endpoint_data.get("method"),
            "host": endpoint_data.get("host"),
            "path": endpoint_data.get("path"),
            "status": "changed" if endpoint_data.get("has_changes") else "unchanged",
            "present_in": endpoint_data.get("present_in", []),
            "missing_in": endpoint_data.get("missing_in", []),
            "differences": {}  # Initialize differences dictionary
        }
        
        # Process differences including request differences
        if endpoint_data.get("has_changes"):
            # Get the original differences
            differences = endpoint_data.get("differences", {})
            
            # Create a copy of the differences to avoid modifying during iteration
            endpoint_summary["differences"] = {
                "request_differences": {},  # Initialize request differences
                "status_codes": differences.get("status_codes", {}),
                "request": differences.get("request", {}),
                "response": differences.get("response", {}),
                "headers": differences.get("headers", {}),
                "parameters": differences.get("parameters", {})
            }
            
            # Process request differences if they exist
            for key, value in differences.items():
                if isinstance(value, dict) and value.get("type") == "value_mismatch":
                    endpoint_summary["differences"]["request_differences"][key] = value
            
            # Create instances dict if needed
            endpoint_summary["differences"]["instances"] = {}
            
            # Add any instance-specific differences
            instance_keys = [k for k in differences.keys() if k.startswith(file_labels[0]) and "_vs_" in k]
            for key in instance_keys:
                endpoint_summary["differences"]["instances"][key] = differences[key]
        
        # Add to endpoints collection
        dashboard_data["endpoints"][endpoint_key] = endpoint_summary
        
        # Categorize by host
        host = endpoint_data.get("host", "unknown")
        if host not in dashboard_data["summary"]["by_host"]:
            dashboard_data["summary"]["by_host"][host] = {
                "total": 0,
                "changed": 0,
                "unchanged": 0,
                "endpoints": []
            }
        
        dashboard_data["summary"]["by_host"][host]["total"] += 1
        dashboard_data["summary"]["by_host"][host]["endpoints"].append(endpoint_key)
        
        if endpoint_data.get("has_changes"):
            dashboard_data["summary"]["by_host"][host]["changed"] += 1
            dashboard_data["summary"]["by_change_type"]["modified"].append(endpoint_key)
        else:
            dashboard_data["summary"]["by_host"][host]["unchanged"] += 1
    
    # Create a unique filename based on timestamp and file labels
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    labels_part = "-".join(file_labels)
    output_file = os.path.join(args.output_dir, f"dashboard_{labels_part}_{timestamp}.json")
    
    # Save the dashboard-ready data
    with open(output_file, 'w') as f:
        json.dump(dashboard_data, f, indent=2)
    
    # Update the index file
    index_file = os.path.join(args.output_dir, "index.json")
    if os.path.exists(index_file):
        with open(index_file, 'r') as f:
            try:
                index_data = json.load(f)
            except json.JSONDecodeError:
                index_data = {"comparisons": []}
    else:
        index_data = {"comparisons": []}
    
    # Add the new comparison to the index
    new_entry = {
        "file": os.path.basename(output_file),
        "timestamp": datetime.now().isoformat(),
        "file_labels": file_labels,
        "metadata": metadata
    }
    
    index_data["comparisons"].append(new_entry)
    index_data["comparisons"].sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Write the updated index
    with open(index_file, 'w') as f:
        json.dump(index_data, f, indent=2)
    
    print(json.dumps({
        "status": "success",
        "message": f"Successfully added comparison to dashboard",
        "dashboard_file": output_file,
        "index_file": index_file
    }, indent=2))

if __name__ == "__main__":
    main() 
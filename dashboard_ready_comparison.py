#!/usr/bin/env python3
import sys
import json
import os
from datetime import datetime
from server import compare_api_structures
import argparse

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Compare API structures and save dashboard-ready format")
    parser.add_argument('--file_paths', type=str, required=True, 
                        help='JSON string array of file paths to compare')
    parser.add_argument('--output_dir', type=str, default="./dashboard_data",
                        help='Directory to save comparison results')
    parser.add_argument('--comparison_level', type=str, default="comprehensive",
                        choices=["basic", "detailed", "comprehensive"],
                        help='Level of detail for comparison')
    parser.add_argument('--metadata', type=str, default="{}",
                        help='JSON string of metadata to include (e.g. version labels)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Parse file_paths from JSON string
    try:
        file_paths = json.loads(args.file_paths)
        if not isinstance(file_paths, list):
            print("Error: file_paths must be a JSON array of strings")
            sys.exit(1)
    except json.JSONDecodeError:
        print("Error: file_paths is not valid JSON")
        sys.exit(1)
    
    # Parse metadata if provided
    try:
        metadata = json.loads(args.metadata)
    except json.JSONDecodeError:
        print("Error: metadata is not valid JSON")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # Extract version labels from filenames or metadata
    file_labels = metadata.get("version_labels", [])
    if not file_labels or len(file_labels) != len(file_paths):
        # Extract labels from filenames if not provided
        file_labels = [os.path.basename(f).split('_')[0] for f in file_paths]
    
    print(f"Comparing files: {file_paths}")
    print(f"Using labels: {file_labels}")
    print(f"Output directory: {args.output_dir}")
    
    # Load and parse the files
    file_data = []
    for file_path in file_paths:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                file_data.append({
                    "data": data,
                    "file_label": os.path.basename(file_path)
                })
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading file {file_path}: {str(e)}")
            sys.exit(1)
    
    # Run the comparison
    result = compare_api_structures(
        file_paths=file_data,
        output_dir=args.output_dir,
        comparison_level=args.comparison_level
    )
    
    # Process the result into dashboard-friendly format
    dashboard_data = process_for_dashboard(result, file_labels, metadata)
    
    # Create a unique filename based on timestamp and file labels
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    labels_part = "-".join(file_labels)
    output_file = os.path.join(args.output_dir, f"api_comparison_{labels_part}_{timestamp}.json")
    
    # Save the dashboard-ready data
    with open(output_file, 'w') as f:
        json.dump(dashboard_data, f, indent=2)
    
    # Generate an index file of all comparisons
    update_index_file(args.output_dir, output_file, file_labels, metadata)
    
    print(json.dumps({
        "status": "success",
        "message": f"Successfully saved dashboard-ready comparison to {output_file}",
        "output_file": output_file,
        "index_file": os.path.join(args.output_dir, "index.json")
    }, indent=2))

def process_for_dashboard(comparison_result, file_labels, metadata):
    """Convert the comparison result into a dashboard-friendly format"""
    # Initialize the dashboard data structure
    dashboard_data = {
        "metadata": {
            "comparison_time": datetime.now().isoformat(),
            "file_labels": file_labels,
            "custom_metadata": metadata,
            "total_endpoints": comparison_result.get("summary", {}).get("total_endpoints", 0),
            "endpoints_with_changes": comparison_result.get("summary", {}).get("endpoints_with_changes", 0)
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
    detailed_results = comparison_result.get("detailed_results", {})
    for endpoint_key, endpoint_data in detailed_results.items():
        # Create endpoint entry
        endpoint_summary = {
            "method": endpoint_data.get("method", ""),
            "host": endpoint_data.get("host", ""),
            "path": endpoint_data.get("path", ""),
            "status": "changed" if endpoint_data.get("has_changes") else "unchanged",
            "present_in": endpoint_data.get("present_in", []),
            "missing_in": endpoint_data.get("missing_in", []),
            "differences": endpoint_data.get("differences", {})
        }
        
        # Add to endpoints collection
        dashboard_data["endpoints"][endpoint_key] = endpoint_summary
        
        # Update summary statistics
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
        
        # Categorize added/removed endpoints
        if len(endpoint_data.get("present_in", [])) == 1:
            if endpoint_data["present_in"][0] == file_labels[0]:
                dashboard_data["summary"]["by_change_type"]["removed"].append(endpoint_key)
            else:
                dashboard_data["summary"]["by_change_type"]["added"].append(endpoint_key)
    
    return dashboard_data

def update_index_file(output_dir, new_file, file_labels, metadata):
    """Update or create an index file listing all comparisons"""
    index_file = os.path.join(output_dir, "index.json")
    
    # Initialize or load the index
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
        "file": os.path.basename(new_file),
        "timestamp": datetime.now().isoformat(),
        "file_labels": file_labels,
        "metadata": metadata
    }
    
    index_data["comparisons"].append(new_entry)
    
    # Sort by timestamp (newest first)
    index_data["comparisons"].sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Write the updated index
    with open(index_file, 'w') as f:
        json.dump(index_data, f, indent=2)

if __name__ == "__main__":
    main() 
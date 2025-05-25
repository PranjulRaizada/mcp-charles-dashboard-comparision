#!/usr/bin/env python3
import json
import os
from datetime import datetime

def compare_api_structures(file_paths, output_dir="./output", comparison_level="detailed"):
    """
    Compare API structures between multiple Charles log files
    
    Args:
        file_paths: List of paths to the parsed JSON files to compare
        output_dir: Directory to save comparison results
        comparison_level: Level of detail for comparison (basic, detailed, comprehensive)
        
    Returns:
        Dictionary containing comparison results
    """
    # Initialize results structure
    results = {
        "summary": {
            "total_endpoints": 0,
            "endpoints_with_changes": 0,
            "comparison_time": datetime.now().isoformat()
        },
        "detailed_results": {}
    }
    
    # Load all files
    file_data = []
    for path in file_paths:
        with open(path, 'r') as f:
            file_data.append(json.load(f))
    
    # Extract and compare endpoints
    all_endpoints = set()
    for data in file_data:
        if isinstance(data, dict) and "endpoints" in data:
            all_endpoints.update(data["endpoints"].keys())
    
    results["summary"]["total_endpoints"] = len(all_endpoints)
    
    # Compare each endpoint across files
    for endpoint in all_endpoints:
        endpoint_result = {
            "present_in": [],
            "missing_in": [],
            "has_changes": False,
            "differences": {}
        }
        
        # Check presence and details in each file
        for i, data in enumerate(file_data):
            if endpoint in data.get("endpoints", {}):
                endpoint_result["present_in"].append(i)
                endpoint_details = data["endpoints"][endpoint]
                
                # Store first occurrence details as reference
                if not endpoint_result.get("method"):
                    endpoint_result.update({
                        "method": endpoint_details.get("method"),
                        "host": endpoint_details.get("host"),
                        "path": endpoint_details.get("path")
                    })
            else:
                endpoint_result["missing_in"].append(i)
        
        if len(endpoint_result["present_in"]) < len(file_data):
            endpoint_result["has_changes"] = True
            results["summary"]["endpoints_with_changes"] += 1
        
        results["detailed_results"][endpoint] = endpoint_result
    
    return results 
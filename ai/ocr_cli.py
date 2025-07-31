#!/usr/bin/env python3
"""
Command line interface for OCR processing
Used by the OCR MCP server to process images
"""

import sys
import json
import argparse
import os
from simple_ocr import SimpleOCR
import asyncio
import numpy as np

# Custom JSON encoder to handle numpy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

async def process_single_file(file_path: str) -> dict:
    """Process a single file and return JSON result"""
    try:
        ocr = SimpleOCR()
        result = await ocr.extract_from_document(file_path)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path
        }

async def process_batch(directory_path: str, limit: int = 10) -> dict:
    """Process multiple files in a directory"""
    try:
        ocr = SimpleOCR()
        
        # Get image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.bmp', '.tiff']
        files = []
        
        for file in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path) and any(file.lower().endswith(ext) for ext in image_extensions):
                files.append(file_path)
        
        files = files[:limit]  # Limit number of files
        
        results = []
        for file_path in files:
            result = await ocr.extract_from_document(file_path)
            results.append(result)
        
        successful = [r for r in results if r.get("success", False)]
        failed = [r for r in results if not r.get("success", False)]
        
        return {
            "success": True,
            "total_files": len(files),
            "successful": len(successful),
            "failed": len(failed),
            "results": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "directory_path": directory_path
        }

def main():
    parser = argparse.ArgumentParser(description='OCR Command Line Interface')
    parser.add_argument('--single', type=str, help='Process a single file')
    parser.add_argument('--batch', type=str, help='Process all images in a directory')
    parser.add_argument('--limit', type=int, default=10, help='Limit number of files in batch processing')
    
    args = parser.parse_args()
    
    if args.single:
        if not os.path.exists(args.single):
            result = {
                "success": False,
                "error": f"File not found: {args.single}",
                "file_path": args.single
            }
        else:
            result = asyncio.run(process_single_file(args.single))
            
    elif args.batch:
        if not os.path.exists(args.batch):
            result = {
                "success": False,
                "error": f"Directory not found: {args.batch}",
                "directory_path": args.batch
            }
        else:
            result = asyncio.run(process_batch(args.batch, args.limit))
    else:
        result = {
            "success": False,
            "error": "Please specify either --single <file> or --batch <directory>"
        }
    
    # Output JSON result
    print(json.dumps(result, indent=2, cls=NumpyEncoder))

if __name__ == "__main__":
    main()
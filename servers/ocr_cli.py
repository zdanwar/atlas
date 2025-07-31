#!/usr/bin/env python3
"""
OCR CLI - Command Line Interface for Document Processing
Part of ATLAS - Automated Text Learning & Analysis System
"""

import sys
import json
import argparse
import os
from pathlib import Path
import traceback
from typing import Dict, List, Any, Optional

# Import OCR libraries
try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
    from pdf2image import convert_from_path
except ImportError as e:
    print(f"Error importing required libraries: {e}", file=sys.stderr)
    print("Please install: pip install pytesseract Pillow opencv-python pdf2image numpy", file=sys.stderr)
    sys.exit(1)

class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

class OCRProcessor:
    """OCR processing engine with Tesseract backend"""
    
    def __init__(self):
        self.setup_tesseract()
    
    def setup_tesseract(self):
        """Configure Tesseract OCR engine"""
        # Check if tesseract is installed
        try:
            tesseract_version = pytesseract.get_tesseract_version()
            print(f"Tesseract version: {tesseract_version}", file=sys.stderr)
        except Exception as e:
            print(f"Error: Tesseract not found. Please install: brew install tesseract", file=sys.stderr)
            raise e
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Preprocess image for better OCR results"""
        try:
            # Try multiple methods to read the image
            img = None
            
            # Method 1: Try OpenCV first
            img = cv2.imread(image_path)
            
            # Method 2: If OpenCV fails, try PIL
            if img is None:
                try:
                    pil_img = Image.open(image_path)
                    # Convert PIL image to OpenCV format
                    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                except Exception as pil_error:
                    print(f"PIL also failed for {image_path}: {pil_error}", file=sys.stderr)
            
            if img is None:
                raise ValueError(f"Could not read image with any method: {image_path}")
            
            # Convert to grayscale
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply threshold for better text recognition
            _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            return thresh
            
        except Exception as e:
            print(f"Error preprocessing image {image_path}: {e}", file=sys.stderr)
            # Last resort fallback
            try:
                return cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            except:
                raise ValueError(f"Complete failure to load image: {image_path}")
    
    def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """Extract text from image using Tesseract OCR"""
        try:
            # Preprocess image
            processed_img = self.preprocess_image(image_path)
            
            # Configure Tesseract
            config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?@#$%^&*()_+-=[]{}|;:\'\"<>/~`'
            
            # Extract text
            text = pytesseract.image_to_string(processed_img, config=config)
            
            # Get detailed data with confidence scores
            data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT)
            
            # Calculate confidence scores
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Extract bounding boxes for words with high confidence
            boxes = []
            for i, conf in enumerate(data['conf']):
                if int(conf) > 30:  # Only include high-confidence text
                    boxes.append({
                        'text': data['text'][i],
                        'confidence': int(conf),
                        'x': int(data['left'][i]),
                        'y': int(data['top'][i]),
                        'width': int(data['width'][i]),
                        'height': int(data['height'][i])
                    })
            
            return {
                'success': True,
                'text': text.strip(),
                'confidence': round(avg_confidence, 2),
                'word_count': len(text.split()),
                'boxes': boxes,
                'image_path': image_path
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'confidence': 0,
                'image_path': image_path
            }
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Process PDF by converting pages to images and running OCR"""
        try:
            # Convert PDF to images
            pages = convert_from_path(pdf_path, dpi=300)
            
            results = []
            combined_text = []
            total_confidence = 0
            
            for i, page in enumerate(pages):
                # Save page as temporary image
                temp_image_path = f"/tmp/pdf_page_{i}.png"
                page.save(temp_image_path, 'PNG')
                
                # Process page with OCR
                page_result = self.extract_text_from_image(temp_image_path)
                page_result['page_number'] = i + 1
                results.append(page_result)
                
                if page_result['success']:
                    combined_text.append(page_result['text'])
                    total_confidence += page_result['confidence']
                
                # Clean up temp file
                try:
                    os.remove(temp_image_path)
                except:
                    pass
            
            avg_confidence = total_confidence / len(results) if results else 0
            
            return {
                'success': True,
                'text': '\n\n--- PAGE BREAK ---\n\n'.join(combined_text),
                'confidence': round(avg_confidence, 2),
                'pages': len(results),
                'page_results': results,
                'pdf_path': pdf_path
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'confidence': 0,
                'pdf_path': pdf_path
            }
    
    def extract_structured_data(self, text: str, document_type: str = 'purchase_order') -> Dict[str, Any]:
        """Extract structured data from OCR text"""
        import re
        
        structured_data = {
            'document_type': document_type,
            'extracted_fields': {}
        }
        
        if document_type == 'purchase_order':
            # Extract common purchase order fields
            patterns = {
                'po_number': [
                    r'P\.?O\.?\s*#?\s*:?\s*(\w+[\w\-\s]*\w+)',
                    r'Purchase Order\s*#?\s*:?\s*(\w+[\w\-\s]*\w+)',
                    r'Order\s*#?\s*:?\s*(\w+[\w\-\s]*\w+)'
                ],
                'invoice_number': [
                    r'Invoice\s*#?\s*:?\s*(\w+[\w\-\s]*\w+)',
                    r'Inv\.?\s*#?\s*:?\s*(\w+[\w\-\s]*\w+)'
                ],
                'date': [
                    r'Date\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                    r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                    r'(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})'
                ],
                'total_amount': [
                    r'Total\s*:?\s*\$?\s*(\d+[,\d]*\.?\d*)',
                    r'Amount\s*:?\s*\$?\s*(\d+[,\d]*\.?\d*)',
                    r'\$\s*(\d+[,\d]*\.?\d*)'
                ],
                'vendor': [
                    r'Vendor\s*:?\s*([A-Za-z\s&\.,]+?)(?:\n|$)',
                    r'From\s*:?\s*([A-Za-z\s&\.,]+?)(?:\n|$)',
                    r'Supplier\s*:?\s*([A-Za-z\s&\.,]+?)(?:\n|$)'
                ]
            }
            
            for field, field_patterns in patterns.items():
                for pattern in field_patterns:
                    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                    if match:
                        structured_data['extracted_fields'][field] = match.group(1).strip()
                        break
        
        return structured_data
    
    def batch_process_images(self, directory: str, document_type: str = 'purchase_order') -> Dict[str, Any]:
        """Process all images in a directory"""
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                return {
                    'success': False,
                    'error': f'Directory does not exist: {directory}',
                    'results': []
                }
            
            # Supported image formats
            image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}
            pdf_extensions = {'.pdf'}
            
            results = []
            
            # Process all supported files
            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    if file_path.suffix.lower() in image_extensions:
                        # Process image
                        result = self.extract_text_from_image(str(file_path))
                        if result['success'] and result['text']:
                            # Extract structured data
                            structured = self.extract_structured_data(result['text'], document_type)
                            result['structured_data'] = structured
                        results.append(result)
                        
                    elif file_path.suffix.lower() in pdf_extensions:
                        # Process PDF
                        result = self.process_pdf(str(file_path))
                        if result['success'] and result['text']:
                            # Extract structured data
                            structured = self.extract_structured_data(result['text'], document_type)
                            result['structured_data'] = structured
                        results.append(result)
            
            successful_results = [r for r in results if r['success']]
            
            return {
                'success': True,
                'total_files': len(results),
                'successful_files': len(successful_results),
                'failed_files': len(results) - len(successful_results),
                'results': results,
                'directory': directory
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'results': [],
                'directory': directory
            }

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='OCR CLI for document processing')
    parser.add_argument('command', choices=['image', 'pdf', 'batch'], help='Processing command')
    parser.add_argument('path', help='Path to image, PDF, or directory')
    parser.add_argument('--document-type', default='purchase_order', help='Document type for structured extraction')
    parser.add_argument('--output', help='Output file for results (JSON format)')
    
    args = parser.parse_args()
    
    try:
        processor = OCRProcessor()
        
        if args.command == 'image':
            result = processor.extract_text_from_image(args.path)
            if result['success'] and result['text']:
                structured = processor.extract_structured_data(result['text'], args.document_type)
                result['structured_data'] = structured
                
        elif args.command == 'pdf':
            result = processor.process_pdf(args.path)
            if result['success'] and result['text']:
                structured = processor.extract_structured_data(result['text'], args.document_type)
                result['structured_data'] = structured
                
        elif args.command == 'batch':
            result = processor.batch_process_images(args.path, args.document_type)
        
        # Output results
        json_output = json.dumps(result, indent=2, cls=NumpyEncoder)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(json_output)
            print(f"Results saved to: {args.output}", file=sys.stderr)
        else:
            print(json_output)
            
    except Exception as e:
        error_result = {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        print(json.dumps(error_result, indent=2), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Enhanced PDF Processing for OCR MCP Server
Supports hybrid text extraction + OCR for complex PDFs
"""

import sys
import os
import io
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image
import numpy as np
try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False
    
# Fallback PDF conversion
try:
    from pdf_fallback import convert_pdf_to_images_fallback
    HAS_FALLBACK = True
except ImportError:
    HAS_FALLBACK = False
import json

# Try to import additional PDF libraries
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

class EnhancedPDFProcessor:
    """Enhanced PDF processor with hybrid text extraction and OCR"""
    
    def __init__(self, cache_dir: str = "./pdf_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Print available PDF libraries
        print("📚 Available PDF Libraries:", file=sys.stderr)
        print(f"   • PyPDF2: {'✅' if HAS_PYPDF2 else '❌'}", file=sys.stderr)
        print(f"   • pdfplumber: {'✅' if HAS_PDFPLUMBER else '❌'}", file=sys.stderr)
        print(f"   • PyMuPDF: {'✅' if HAS_PYMUPDF else '❌'}", file=sys.stderr)
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract text directly from PDF (for text-based PDFs)"""
        extracted_text = []
        method_used = "none"
        
        # Method 1: Try PyMuPDF (fastest and most accurate)
        if HAS_PYMUPDF:
            try:
                doc = fitz.open(pdf_path)
                for page_num in range(min(len(doc), 20)):  # Limit to 20 pages
                    page = doc[page_num]
                    text = page.get_text()
                    if text.strip():
                        extracted_text.append({
                            "page": page_num + 1,
                            "text": text.strip(),
                            "method": "PyMuPDF"
                        })
                doc.close()
                method_used = "PyMuPDF"
                if extracted_text:
                    print(f"✅ Extracted text from {len(extracted_text)} pages using PyMuPDF", file=sys.stderr)
                    return {"success": True, "text_pages": extracted_text, "method": method_used}
            except Exception as e:
                print(f"⚠️  PyMuPDF failed: {e}", file=sys.stderr)
        
        # Method 2: Try pdfplumber (good for tables and structured data)
        if HAS_PDFPLUMBER and not extracted_text:
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages[:20]):  # Limit to 20 pages
                        text = page.extract_text()
                        if text and text.strip():
                            extracted_text.append({
                                "page": page_num + 1,
                                "text": text.strip(),
                                "method": "pdfplumber"
                            })
                method_used = "pdfplumber"
                if extracted_text:
                    print(f"✅ Extracted text from {len(extracted_text)} pages using pdfplumber", file=sys.stderr)
                    return {"success": True, "text_pages": extracted_text, "method": method_used}
            except Exception as e:
                print(f"⚠️  pdfplumber failed: {e}", file=sys.stderr)
        
        # Method 3: Try PyPDF2 (basic fallback)
        if HAS_PYPDF2 and not extracted_text:
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page_num in range(min(len(pdf_reader.pages), 20)):
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        if text and text.strip():
                            extracted_text.append({
                                "page": page_num + 1,
                                "text": text.strip(),
                                "method": "PyPDF2"
                            })
                method_used = "PyPDF2"
                if extracted_text:
                    print(f"✅ Extracted text from {len(extracted_text)} pages using PyPDF2", file=sys.stderr)
                    return {"success": True, "text_pages": extracted_text, "method": method_used}
            except Exception as e:
                print(f"⚠️  PyPDF2 failed: {e}", file=sys.stderr)
        
        return {"success": False, "text_pages": [], "method": "none", "error": "No text extraction method succeeded"}
    
    def convert_pdf_to_images(self, pdf_path: str, dpi: int = 300, max_pages: int = 20) -> Tuple[List[Image.Image], Dict]:
        """Convert PDF to high-quality images for OCR"""
        conversion_info = {
            "success": False,
            "pages_converted": 0,
            "dpi_used": dpi,
            "method": "unknown"
        }
        
        images = []
        
        # Try pdf2image first (requires poppler)
        if HAS_PDF2IMAGE:
            try:
                print(f"🖼️  Converting PDF to images at {dpi} DPI...", file=sys.stderr)
                
                # Higher DPI for better OCR accuracy, but limit pages for performance
                images = convert_from_path(
                    pdf_path, 
                    dpi=dpi,
                    first_page=1, 
                    last_page=max_pages,
                    fmt='PNG'  # PNG for better quality
                )
                
                conversion_info.update({
                    "success": True,
                    "pages_converted": len(images),
                    "method": "pdf2image",
                    "total_size_mb": sum(
                        len(np.array(img).tobytes()) for img in images
                    ) / (1024 * 1024)
                })
                
                print(f"✅ Converted {len(images)} pages to images ({conversion_info['total_size_mb']:.1f}MB)", file=sys.stderr)
                return images, conversion_info
                
            except Exception as e:
                conversion_info["error"] = str(e)
                print(f"⚠️  pdf2image failed: {e}", file=sys.stderr)
        
        # Try PyMuPDF fallback
        if not images and (HAS_FALLBACK or HAS_PYMUPDF):
            try:
                print(f"🔄 Using PyMuPDF fallback for PDF conversion...", file=sys.stderr)
                
                if HAS_FALLBACK:
                    images = convert_pdf_to_images_fallback(pdf_path, dpi=dpi, max_pages=max_pages)
                    conversion_info["method"] = "pymupdf_fallback"
                else:
                    # Direct PyMuPDF conversion
                    doc = fitz.open(pdf_path)
                    for page_num in range(min(len(doc), max_pages)):
                        page = doc[page_num]
                        mat = fitz.Matrix(dpi/72.0, dpi/72.0)
                        pix = page.get_pixmap(matrix=mat, alpha=False)
                        img_data = pix.tobytes("png")
                        img = Image.open(io.BytesIO(img_data))
                        images.append(img)
                    doc.close()
                    conversion_info["method"] = "pymupdf_direct"
                
                if images:
                    conversion_info.update({
                        "success": True,
                        "pages_converted": len(images),
                        "total_size_mb": sum(
                            len(np.array(img).tobytes()) for img in images
                        ) / (1024 * 1024)
                    })
                    
                    print(f"✅ Converted {len(images)} pages using PyMuPDF", file=sys.stderr)
                    return images, conversion_info
                    
            except Exception as e:
                conversion_info["error"] = str(e)
                print(f"❌ PyMuPDF conversion also failed: {e}", file=sys.stderr)
        
        # If all methods failed
        if not images:
            conversion_info["error"] = conversion_info.get("error", "No PDF conversion method available")
            print(f"❌ All PDF conversion methods failed", file=sys.stderr)
            
        return images, conversion_info
    
    def analyze_pdf_content(self, pdf_path: str) -> Dict[str, Any]:
        """Analyze PDF to determine best processing strategy"""
        analysis = {
            "file_size_mb": os.path.getsize(pdf_path) / (1024 * 1024),
            "is_text_based": False,
            "is_image_based": False,
            "is_hybrid": False,
            "page_count": 0,
            "recommended_strategy": "ocr_only"
        }
        
        # Get basic PDF info
        try:
            if HAS_PYMUPDF:
                doc = fitz.open(pdf_path)
                analysis["page_count"] = len(doc)
                
                # Check first few pages for text content
                text_pages = 0
                image_pages = 0
                
                for page_num in range(min(5, len(doc))):  # Check first 5 pages
                    page = doc[page_num]
                    text = page.get_text().strip()
                    images = page.get_images()
                    
                    if len(text) > 50:  # Significant text content
                        text_pages += 1
                    if images:  # Has images
                        image_pages += 1
                
                doc.close()
                
                # Determine content type
                if text_pages > 0 and image_pages > 0:
                    analysis["is_hybrid"] = True
                    analysis["recommended_strategy"] = "hybrid"
                elif text_pages > 0:
                    analysis["is_text_based"] = True
                    analysis["recommended_strategy"] = "text_extraction"
                else:
                    analysis["is_image_based"] = True
                    analysis["recommended_strategy"] = "ocr_only"
                    
            else:
                # Fallback analysis
                analysis["recommended_strategy"] = "ocr_only"
                
        except Exception as e:
            print(f"⚠️  PDF analysis failed: {e}", file=sys.stderr)
            analysis["error"] = str(e)
        
        return analysis
    
    def process_pdf_hybrid(self, pdf_path: str, ocr_processor=None) -> Dict[str, Any]:
        """Process PDF using hybrid approach (text extraction + OCR)"""
        print(f"📄 Processing PDF with hybrid approach: {os.path.basename(pdf_path)}", file=sys.stderr)
        
        # Analyze PDF first
        analysis = self.analyze_pdf_content(pdf_path)
        print(f"📊 PDF Analysis: {analysis['recommended_strategy']} - {analysis['page_count']} pages", file=sys.stderr)
        
        result = {
            "success": False,
            "file_path": pdf_path,
            "file_name": os.path.basename(pdf_path),
            "pdf_analysis": analysis,
            "processing_method": analysis["recommended_strategy"],
            "pages": [],
            "combined_text": "",
            "structured_data": {}
        }
        
        try:
            if analysis["recommended_strategy"] == "text_extraction":
                # Pure text extraction
                text_result = self.extract_text_from_pdf(pdf_path)
                if text_result["success"]:
                    for page_data in text_result["text_pages"]:
                        result["pages"].append({
                            "page_number": page_data["page"],
                            "extraction_method": "text",
                            "text": page_data["text"],
                            "confidence": 1.0  # Text extraction is 100% accurate
                        })
                    result["combined_text"] = " ".join(page["text"] for page in result["pages"])
                    result["success"] = True
                    
            elif analysis["recommended_strategy"] == "hybrid":
                # Try text extraction first, then OCR for image-heavy pages
                text_result = self.extract_text_from_pdf(pdf_path)
                ocr_pages = []
                
                if text_result["success"]:
                    # Add text-extracted pages
                    for page_data in text_result["text_pages"]:
                        result["pages"].append({
                            "page_number": page_data["page"],
                            "extraction_method": "text",
                            "text": page_data["text"],
                            "confidence": 1.0
                        })
                
                # For pages without sufficient text, use OCR
                if ocr_processor and analysis["page_count"] > len(text_result.get("text_pages", [])):
                    print("🔍 Using OCR for image-heavy pages...", file=sys.stderr)
                    images, conversion_info = self.convert_pdf_to_images(pdf_path, dpi=250, max_pages=10)
                    
                    if images and ocr_processor:
                        for i, image in enumerate(images):
                            page_num = i + 1
                            # Skip pages we already have text for
                            if not any(p["page_number"] == page_num for p in result["pages"]):
                                ocr_result = ocr_processor._extract_text_with_structure(image)
                                result["pages"].append({
                                    "page_number": page_num,
                                    "extraction_method": "ocr",
                                    "text": ocr_result["full_text"],
                                    "confidence": ocr_result.get("avg_confidence", 0.8),
                                    "text_blocks": len(ocr_result.get("text_blocks", []))
                                })
                
                # Sort pages by page number
                result["pages"].sort(key=lambda x: x["page_number"])
                result["combined_text"] = " ".join(page["text"] for page in result["pages"])
                result["success"] = True
                
            else:
                # OCR only for image-based PDFs
                if ocr_processor:
                    print("🔍 Using OCR-only approach...", file=sys.stderr)
                    images, conversion_info = self.convert_pdf_to_images(pdf_path)
                    result["conversion_info"] = conversion_info
                    
                    if images:
                        for i, image in enumerate(images):
                            ocr_result = ocr_processor._extract_text_with_structure(image)
                            result["pages"].append({
                                "page_number": i + 1,
                                "extraction_method": "ocr",
                                "text": ocr_result["full_text"],
                                "confidence": ocr_result.get("avg_confidence", 0.8),
                                "text_blocks": len(ocr_result.get("text_blocks", [])),
                                "ocr_details": ocr_result
                            })
                        
                        result["combined_text"] = " ".join(page["text"] for page in result["pages"])
                        result["success"] = True
                else:
                    result["error"] = "OCR processor not available"
            
            # Extract structured data if successful
            if result["success"] and result["combined_text"]:
                result["structured_data"] = self.extract_pdf_structured_data(result["combined_text"], analysis)
                
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ Hybrid PDF processing failed: {e}", file=sys.stderr)
        
        return result
    
    def extract_pdf_structured_data(self, text: str, pdf_analysis: Dict) -> Dict[str, Any]:
        """Extract structured data specifically for PDF documents"""
        import re
        from datetime import datetime
        
        structured = {
            "document_type": "PDF Document",
            "invoice_number": None,
            "po_number": None,  
            "vendor_name": None,
            "total_amount": None,
            "date": None,
            "line_items": [],
            "contact_info": {}
        }
        
        text_lower = text.lower()
        
        # Enhanced PDF-specific patterns
        
        # Invoice/Document number patterns
        invoice_patterns = [
            r'invoice\s*(?:no\.?|number)?\s*:?\s*([A-Za-z0-9\-\/]+)',
            r'bill\s*(?:no\.?|number)?\s*:?\s*([A-Za-z0-9\-\/]+)',
            r'document\s*(?:no\.?|number)?\s*:?\s*([A-Za-z0-9\-\/]+)'
        ]
        
        for pattern in invoice_patterns:
            match = re.search(pattern, text_lower)
            if match:
                structured["invoice_number"] = match.group(1).upper()
                break
        
        # PO number patterns
        po_patterns = [
            r'po\s*(?:no\.?|number)?\s*:?\s*([A-Za-z0-9\-\/]+)',
            r'purchase\s*order\s*(?:no\.?|number)?\s*:?\s*([A-Za-z0-9\-\/]+)',
            r'p\.o\.?\s*(?:no\.?|number)?\s*:?\s*([A-Za-z0-9\-\/]+)'
        ]
        
        for pattern in po_patterns:
            match = re.search(pattern, text_lower)
            if match:
                structured["po_number"] = match.group(1).upper()
                break
        
        # Company/Vendor name (look for "To:" or first few lines)
        lines = text.split('\n')[:10]
        for line in lines:
            line = line.strip()
            if len(line) > 5 and not any(keyword in line.lower() for keyword in 
                ['invoice', 'bill', 'po no', 'date', 'total', 'amount']):
                if structured["vendor_name"] is None or len(line) > len(structured["vendor_name"]):
                    structured["vendor_name"] = line
        
        # Enhanced amount detection
        amount_patterns = [
            r'total\s*(?:amount)?\s*:?\s*(?:rs\.?|₹|\$)?\s*([0-9,]+\.?\d*)',
            r'grand\s*total\s*:?\s*(?:rs\.?|₹|\$)?\s*([0-9,]+\.?\d*)',
            r'net\s*amount\s*:?\s*(?:rs\.?|₹|\$)?\s*([0-9,]+\.?\d*)',
            r'(?:rs\.?|₹|\$)\s*([0-9,]+\.?\d*)\s*(?:total|grand|net)?'
        ]
        
        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, text_lower)
            amounts.extend(matches)
        
        if amounts:
            # Convert amounts to float and find the largest (likely the total)
            numeric_amounts = []
            for amt in amounts:
                try:
                    numeric_amounts.append(float(amt.replace(',', '')))
                except:
                    pass
            if numeric_amounts:
                structured["total_amount"] = str(max(numeric_amounts))
        
        # Date patterns
        date_patterns = [
            r'date\s*:?\s*(\d{1,2}[-\/\.]\d{1,2}[-\/\.]\d{2,4})',
            r'dated?\s*:?\s*(\d{1,2}[-\/\.]\d{1,2}[-\/\.]\d{2,4})',
            r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text_lower)
            if match:
                structured["date"] = match.group(1)
                break
        
        # Contact information
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        phone_pattern = r'(\+?\d{1,4}[\s-]?\(?\d{3,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,9})'
        
        emails = re.findall(email_pattern, text)
        phones = re.findall(phone_pattern, text)
        
        if emails:
            structured["contact_info"]["email"] = emails[0]
        if phones:
            structured["contact_info"]["phone"] = phones[0]
        
        return structured

def test_pdf_processor():
    """Test the enhanced PDF processor"""
    processor = EnhancedPDFProcessor()
    
    test_pdf = "/Users/macbookpro/Documents/Odoo MCP/purchase/SMARLTINKS INV NO 30355 DT 21.04.2025.pdf"
    
    if os.path.exists(test_pdf):
        print("🧪 Testing Enhanced PDF Processor")
        print("=" * 40)
        
        # Test analysis
        analysis = processor.analyze_pdf_content(test_pdf)
        print(f"Analysis: {json.dumps(analysis, indent=2)}")
        
        # Test text extraction
        text_result = processor.extract_text_from_pdf(test_pdf)
        print(f"\nText Extraction Success: {text_result['success']}")
        if text_result['success']:
            print(f"Extracted from {len(text_result['text_pages'])} pages using {text_result['method']}")
    else:
        print(f"Test PDF not found: {test_pdf}")

if __name__ == "__main__":
    test_pdf_processor()
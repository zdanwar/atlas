import easyocr
import numpy as np
from PIL import Image, ImageEnhance
import sys

# Enable HEIF support for iPhone images
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    print("Warning: pillow-heif not available. HEIF images may not work.", file=sys.stderr)

# Pillow compatibility fix
try:
    from PIL import Image
    if not hasattr(Image, 'ANTIALIAS'):
        Image.ANTIALIAS = Image.LANCZOS
except ImportError:
    pass

import cv2
import PyPDF2
from pdf2image import convert_from_path
import os
import hashlib
import pickle
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

# Import enhanced PDF processor
try:
    from enhanced_pdf_processor import EnhancedPDFProcessor
    HAS_ENHANCED_PDF = True
except ImportError:
    HAS_ENHANCED_PDF = False
    print("Warning: Enhanced PDF processor not available.", file=sys.stderr)

class SimpleOCR:
    def __init__(self, cache_dir: str = "./ocr_cache"):
        """Initialize simple OCR processor"""
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize OCR engine
        print("Initializing OCR engine...", file=sys.stderr)
        self.reader = easyocr.Reader(['en'], gpu=True)  # GPU acceleration enabled
        print("OCR engine ready!", file=sys.stderr)
        
        # Initialize enhanced PDF processor if available
        if HAS_ENHANCED_PDF:
            self.pdf_processor = EnhancedPDFProcessor(cache_dir=os.path.join(cache_dir, "pdf"))
            print("📚 Enhanced PDF processor available!", file=sys.stderr)
        else:
            self.pdf_processor = None
    
    def _get_cache_key(self, file_path: str) -> str:
        """Generate cache key based on file content and modification time"""
        stat = os.stat(file_path)
        with open(file_path, 'rb') as f:
            content_hash = hashlib.md5(f.read()).hexdigest()
        return f"{content_hash}_{int(stat.st_mtime)}"
    
    def _get_cached_result(self, file_path: str) -> Optional[Dict]:
        """Get cached OCR result if exists"""
        cache_key = self._get_cache_key(file_path)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        return None
    
    def _cache_result(self, file_path: str, result: Dict):
        """Cache OCR result"""
        cache_key = self._get_cache_key(file_path)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
        except Exception as e:
            print(f"Failed to cache result: {e}")
    
    def _convert_pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """Convert PDF pages to images"""
        try:
            images = convert_from_path(pdf_path, dpi=200, first_page=1, last_page=10)  # Limit to first 10 pages
            return images
        except Exception as e:
            print(f"Error converting PDF: {e}")
            return []
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Optimize image for OCR"""
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if too large (for speed)
        if max(image.size) > 2500:
            image.thumbnail((2500, 2500), Image.Resampling.LANCZOS)
        
        # Convert to numpy for OpenCV processing
        img_np = np.array(image)
        
        # Simple enhancement for better OCR
        # Convert to grayscale
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # Convert back to PIL Image
        return Image.fromarray(enhanced)
    
    def _extract_text_with_structure(self, image: Image.Image) -> Dict:
        """Extract text with positional and structural information"""
        image_np = np.array(image)
        ocr_results = self.reader.readtext(image_np)
        
        extracted_data = []
        all_text = []
        
        for (bbox, text, confidence) in ocr_results:
            if confidence > 0.5:  # Filter low confidence
                # Calculate position metrics
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                
                text_item = {
                    "text": text.strip(),
                    "confidence": round(confidence, 3),
                    "bbox": bbox,
                    "position": {
                        "x_min": int(min(x_coords)),
                        "x_max": int(max(x_coords)),
                        "y_min": int(min(y_coords)),
                        "y_max": int(max(y_coords)),
                        "width": int(max(x_coords) - min(x_coords)),
                        "height": int(max(y_coords) - min(y_coords))
                    }
                }
                
                extracted_data.append(text_item)
                all_text.append(text.strip())
        
        # Sort by reading order (top to bottom, left to right)
        extracted_data.sort(key=lambda x: (x["position"]["y_min"], x["position"]["x_min"]))
        
        # Create simple structure analysis
        rows = self._group_into_rows(extracted_data)
        
        return {
            "text_blocks": extracted_data,
            "full_text": " ".join(all_text),
            "rows": rows,
            "total_blocks": len(extracted_data),
            "avg_confidence": round(sum(item["confidence"] for item in extracted_data) / len(extracted_data), 3) if extracted_data else 0
        }
    
    def _group_into_rows(self, extracted_data: List[Dict]) -> List[List[Dict]]:
        """Group text blocks into rows based on Y positions"""
        if not extracted_data:
            return []
        
        rows = []
        current_row = [extracted_data[0]]
        current_y = extracted_data[0]["position"]["y_min"]
        
        for item in extracted_data[1:]:
            item_y = item["position"]["y_min"]
            
            # If Y position is close (within 30 pixels), it's same row
            if abs(item_y - current_y) <= 30:
                current_row.append(item)
            else:
                # Sort current row by X position (left to right)
                current_row.sort(key=lambda x: x["position"]["x_min"])
                rows.append(current_row)
                
                # Start new row
                current_row = [item]
                current_y = item_y
        
        # Add the last row
        if current_row:
            current_row.sort(key=lambda x: x["position"]["x_min"])
            rows.append(current_row)
        
        return rows
    
    async def extract_from_document(self, file_path: str) -> Dict[str, Any]:
        """Main method to extract text from any document"""
        try:
            # Check cache first
            cached_result = self._get_cached_result(file_path)
            if cached_result:
                print(f"✅ Using cached result for {os.path.basename(file_path)}", file=sys.stderr)
                return cached_result
            
            print(f"🔍 Processing {os.path.basename(file_path)}...", file=sys.stderr)
            
            file_ext = os.path.splitext(file_path)[1].lower()
            images = []
            
            # Handle different file types
            if file_ext == '.pdf':
                # Use enhanced PDF processor if available
                if self.pdf_processor:
                    print("📄 Using enhanced PDF processor...", file=sys.stderr)
                    pdf_result = self.pdf_processor.process_pdf_hybrid(file_path, ocr_processor=self)
                    
                    if pdf_result["success"]:
                        # Convert enhanced PDF result to our standard format
                        pages_data = []
                        all_text = []
                        
                        for page in pdf_result["pages"]:
                            page_data = {
                                "full_text": page["text"],
                                "text_blocks": [],
                                "rows": [],
                                "total_blocks": 0,
                                "avg_confidence": page.get("confidence", 0.9),
                                "page_number": page["page_number"],
                                "extraction_method": page["extraction_method"]
                            }
                            
                            # If OCR was used, include OCR details
                            if page["extraction_method"] == "ocr" and "ocr_details" in page:
                                ocr_details = page["ocr_details"]
                                page_data["text_blocks"] = ocr_details.get("text_blocks", [])
                                page_data["rows"] = ocr_details.get("rows", [])
                                page_data["total_blocks"] = ocr_details.get("total_text_blocks", 0)
                            
                            pages_data.append(page_data)
                            all_text.append(page["text"])
                        
                        # Create final result
                        result = {
                            "success": True,
                            "file_path": file_path,
                            "file_name": os.path.basename(file_path),
                            "file_type": file_ext,
                            "total_pages": len(pages_data),
                            "pages": pages_data,
                            "combined": {
                                "full_text": " ".join(all_text),
                                "text_blocks": [],
                                "rows": [],
                                "total_text_blocks": sum(p.get("total_blocks", 0) for p in pages_data)
                            },
                            "processing_time": datetime.now().isoformat(),
                            "pdf_analysis": pdf_result.get("pdf_analysis", {}),
                            "processing_method": pdf_result.get("processing_method", "hybrid"),
                            "structured_data": pdf_result.get("structured_data", {})
                        }
                        
                        # Cache and return the result
                        self._cache_result(file_path, result)
                        print(f"✅ Processed PDF with {result['processing_method']} method", file=sys.stderr)
                        return result
                    else:
                        # Fallback to basic PDF processing
                        print("⚠️  Enhanced PDF processing failed, using basic method", file=sys.stderr)
                        images = self._convert_pdf_to_images(file_path)
                else:
                    # Use basic PDF processing
                    images = self._convert_pdf_to_images(file_path)
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.heic', '.heif']:
                try:
                    images = [Image.open(file_path)]
                except Exception as e:
                    # Try to detect if it's actually a HEIF file with wrong extension
                    try:
                        with open(file_path, 'rb') as f:
                            header = f.read(12)
                        if b'ftyp' in header and (b'heic' in header or b'mif1' in header):
                            # It's a HEIF file, try to open it
                            images = [Image.open(file_path)]
                        else:
                            raise e
                    except Exception:
                        return {
                            "success": False,
                            "error": f"Cannot open image file: {str(e)}",
                            "file_path": file_path
                        }
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file type: {file_ext}",
                    "file_path": file_path
                }
            
            if not images:
                return {
                    "success": False,
                    "error": "Could not load images from file",
                    "file_path": file_path
                }
            
            # Process all pages/images
            pages_data = []
            all_text = []
            
            for i, image in enumerate(images):
                print(f"  📄 Processing page {i+1}/{len(images)}...", file=sys.stderr)
                
                # Preprocess image
                processed_image = self._preprocess_image(image)
                
                # Extract text with structure
                page_data = self._extract_text_with_structure(processed_image)
                page_data["page_number"] = i + 1
                
                pages_data.append(page_data)
                all_text.append(page_data["full_text"])
            
            # Combine results
            all_text_blocks = []
            all_rows = []
            
            for page in pages_data:
                all_text_blocks.extend(page["text_blocks"])
                all_rows.extend(page["rows"])
            
            result = {
                "success": True,
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_type": file_ext,
                "total_pages": len(images),
                "pages": pages_data,
                "combined": {
                    "full_text": " ".join(all_text),
                    "text_blocks": all_text_blocks,
                    "rows": all_rows,
                    "total_text_blocks": len(all_text_blocks)
                },
                "processing_time": datetime.now().isoformat()
            }
            
            # Cache the result
            self._cache_result(file_path, result)
            
            print(f"✅ Extracted {len(all_text_blocks)} text blocks from {len(images)} pages", file=sys.stderr)
            return result
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {str(e)}", file=sys.stderr)
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }
    
    async def batch_process(self, directory_path: str, file_patterns: List[str] = None) -> Dict[str, Any]:
        """Process multiple files in a directory"""
        if file_patterns is None:
            file_patterns = ['*.jpg', '*.jpeg', '*.png', '*.pdf']
        
        import glob
        
        all_files = []
        for pattern in file_patterns:
            full_pattern = os.path.join(directory_path, pattern)
            all_files.extend(glob.glob(full_pattern))
        
        print(f"🚀 Processing {len(all_files)} files...", file=sys.stderr)
        
        results = []
        for file_path in all_files:
            result = await self.extract_from_document(file_path)
            results.append(result)
        
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        return {
            "total_files": len(all_files),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
            "batch_processing_time": datetime.now().isoformat()
        }

# Test function
async def test_simple_ocr():
    """Test the simple OCR processor"""
    ocr = SimpleOCR()
    
    # Test single file
    test_file = "/Users/macbookpro/Documents/Odoo MCP/purchase/IMG_2444.jpeg"
    
    if os.path.exists(test_file):
        result = await ocr.extract_from_document(test_file)
        
        if result["success"]:
            print(f"\n=== OCR Results ===")
            print(f"File: {result['file_name']}")
            print(f"Pages: {result['total_pages']}")
            print(f"Text blocks: {result['combined']['total_text_blocks']}")
            print(f"Rows detected: {len(result['combined']['rows'])}")
            print(f"\nFirst few text blocks:")
            for i, block in enumerate(result['combined']['text_blocks'][:5]):
                print(f"{i+1}. {block['text']} (confidence: {block['confidence']})")
        else:
            print(f"Error: {result['error']}")

if __name__ == "__main__":
    asyncio.run(test_simple_ocr())
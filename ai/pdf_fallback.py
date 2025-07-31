#!/usr/bin/env python3
"""
PDF processing fallback when poppler is not available
Uses PyMuPDF to convert PDF to images
"""

import fitz  # PyMuPDF
from PIL import Image
import io
import os
from typing import List

def convert_pdf_to_images_fallback(pdf_path: str, dpi: int = 300, max_pages: int = 20) -> List[Image.Image]:
    """Convert PDF to images using PyMuPDF when poppler is not available"""
    images = []
    
    try:
        doc = fitz.open(pdf_path)
        
        for page_num in range(min(len(doc), max_pages)):
            page = doc[page_num]
            
            # Render page to image
            mat = fitz.Matrix(dpi/72.0, dpi/72.0)  # Create transformation matrix for DPI
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
            
            print(f"✅ Converted page {page_num + 1}/{min(len(doc), max_pages)}", end='\r')
        
        doc.close()
        print(f"\n✅ Successfully converted {len(images)} pages using PyMuPDF")
        
    except Exception as e:
        print(f"❌ PyMuPDF conversion failed: {e}")
        
    return images

if __name__ == "__main__":
    # Test with sample PDF
    test_pdf = "/Users/macbookpro/Documents/Odoo MCP/purchase/SMARLTINKS INV NO 30355 DT 21.04.2025.pdf"
    if os.path.exists(test_pdf):
        images = convert_pdf_to_images_fallback(test_pdf, dpi=200, max_pages=2)
        print(f"Converted {len(images)} pages")
        if images:
            print(f"First page size: {images[0].size}")
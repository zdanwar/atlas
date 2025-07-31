#!/usr/bin/env python3
"""
Simple GPU test for OCR
"""

import time
import torch
from PIL import Image
from pillow_heif import register_heif_opener
import easyocr

# Fix PIL compatibility
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

register_heif_opener()

def test_gpu_availability():
    print("🔬 GPU Acceleration Test")
    print("=" * 30)
    
    # Check PyTorch MPS
    print(f"MPS Available: {torch.backends.mps.is_available()}")
    print(f"MPS Built: {torch.backends.mps.is_built()}")
    
    # Test EasyOCR with GPU
    print("\n📱 Testing HEIF Image Loading...")
    img_path = "/Users/macbookpro/Documents/Odoo MCP/purchase/IMG_2444.jpeg"
    
    try:
        img = Image.open(img_path)
        print(f"✅ HEIF Image loaded: {img.size}")
        
        # Resize for faster testing
        test_img = img.resize((800, 600))
        test_img.save("/tmp/test_small.jpg", "JPEG")
        print("✅ Test image created")
        
    except Exception as e:
        print(f"❌ Image loading failed: {e}")
        return
    
    print("\n🚀 Testing GPU OCR Performance...")
    
    try:
        start_time = time.time()
        reader = easyocr.Reader(['en'], gpu=True)
        init_time = time.time() - start_time
        print(f"   GPU Reader initialized in {init_time:.2f}s")
        
        start_time = time.time()
        result = reader.readtext("/tmp/test_small.jpg")
        ocr_time = time.time() - start_time
        print(f"   OCR processing took {ocr_time:.2f}s")
        print(f"   Found {len(result)} text regions")
        
        if result:
            print(f"   Sample text: {result[0][1][:50]}...")
        
        print("✅ GPU OCR is working!")
        
    except Exception as e:
        print(f"❌ GPU OCR failed: {e}")
        
        # Fallback to CPU test
        print("\n🖥️  Testing CPU OCR as fallback...")
        try:
            start_time = time.time()
            reader_cpu = easyocr.Reader(['en'], gpu=False)
            init_time = time.time() - start_time
            print(f"   CPU Reader initialized in {init_time:.2f}s")
            
            start_time = time.time()
            result = reader_cpu.readtext("/tmp/test_small.jpg")
            ocr_time = time.time() - start_time
            print(f"   CPU OCR processing took {ocr_time:.2f}s")
            print("✅ CPU OCR is working as fallback")
            
        except Exception as e2:
            print(f"❌ CPU OCR also failed: {e2}")

if __name__ == "__main__":
    test_gpu_availability()
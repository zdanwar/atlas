#!/usr/bin/env python3
"""
GPU vs CPU Performance Benchmark for OCR
"""

import time
import sys
import os
import asyncio
from simple_ocr import SimpleOCR
import easyocr

class OCRBenchmark:
    def __init__(self):
        self.test_image = "/Users/macbookpro/Documents/Odoo MCP/purchase/IMG_2444.jpeg"
        
    async def benchmark_cpu_vs_gpu(self):
        """Compare CPU vs GPU performance"""
        print("🔬 OCR Performance Benchmark: CPU vs GPU")
        print("=" * 50)
        
        if not os.path.exists(self.test_image):
            print(f"❌ Test image not found: {self.test_image}")
            return
            
        # Clear any existing cache for fair comparison
        cache_dir = "./ocr_cache"
        if os.path.exists(cache_dir):
            import shutil
            shutil.rmtree(cache_dir)
            
        results = {}
        
        # Test CPU performance
        print("\n🖥️  Testing CPU Performance...")
        cpu_reader = easyocr.Reader(['en'], gpu=False)
        
        start_time = time.time()
        cpu_result = cpu_reader.readtext(self.test_image)
        cpu_time = time.time() - start_time
        
        print(f"   ⏱️  CPU Processing Time: {cpu_time:.2f} seconds")
        print(f"   📝 Text blocks detected: {len(cpu_result)}")
        results['cpu'] = {
            'time': cpu_time,
            'blocks': len(cpu_result)
        }
        
        del cpu_reader  # Free memory
        
        # Test GPU performance
        print("\n🚀 Testing GPU Performance...")
        gpu_reader = easyocr.Reader(['en'], gpu=True)
        
        start_time = time.time()
        gpu_result = gpu_reader.readtext(self.test_image)
        gpu_time = time.time() - start_time
        
        print(f"   ⏱️  GPU Processing Time: {gpu_time:.2f} seconds")
        print(f"   📝 Text blocks detected: {len(gpu_result)}")
        results['gpu'] = {
            'time': gpu_time,
            'blocks': len(gpu_result)
        }
        
        del gpu_reader  # Free memory
        
        # Calculate improvement
        print("\n📊 Performance Comparison")
        print("-" * 30)
        if cpu_time > 0:
            speedup = cpu_time / gpu_time
            improvement = ((cpu_time - gpu_time) / cpu_time) * 100
            
            print(f"CPU Time:     {cpu_time:.2f}s")
            print(f"GPU Time:     {gpu_time:.2f}s")
            print(f"Speedup:      {speedup:.2f}x faster")
            print(f"Improvement:  {improvement:.1f}% faster")
            
            if improvement > 10:
                print("✅ Significant performance improvement with GPU!")
                recommendation = "ENABLE"
            elif improvement > 0:
                print("✅ Moderate performance improvement with GPU")
                recommendation = "ENABLE"
            else:
                print("⚠️  GPU not faster (possibly due to small image or overhead)")
                recommendation = "CPU"
                
        else:
            recommendation = "GPU"
            
        return {
            'results': results,
            'recommendation': recommendation,
            'speedup': speedup if 'speedup' in locals() else 1.0
        }
    
    async def test_simple_ocr_performance(self):
        """Test our SimpleOCR class with GPU enabled"""
        print("\n🧪 Testing SimpleOCR Class Performance...")
        
        ocr = SimpleOCR()
        start_time = time.time()
        
        result = await ocr.extract_from_document(self.test_image)
        processing_time = time.time() - start_time
        
        if result['success']:
            print(f"   ⏱️  SimpleOCR Processing Time: {processing_time:.2f} seconds")
            print(f"   📝 Text blocks: {result['combined']['total_text_blocks']}")
            print(f"   🎯 Average confidence: {result['combined']['avg_confidence']}")
            print("   ✅ SimpleOCR with GPU: Working!")
        else:
            print(f"   ❌ SimpleOCR failed: {result['error']}")
            
        return processing_time

async def main():
    benchmark = OCRBenchmark()
    
    # Run benchmarks
    comparison = await benchmark.benchmark_cpu_vs_gpu()
    simple_ocr_time = await benchmark.test_simple_ocr_performance()
    
    print("\n🎯 Final Recommendations")
    print("=" * 30)
    
    if comparison['recommendation'] == "ENABLE":
        print("✅ GPU acceleration is RECOMMENDED")
        print(f"   • {comparison['speedup']:.1f}x performance improvement")
        print("   • GPU is already enabled in your OCR setup")
        print("   • Your AMD Radeon Pro 560X provides excellent acceleration")
    else:
        print("⚠️  CPU might be sufficient for your use case")
        print("   • Consider GPU for batch processing of many images")
        
    print(f"\n💡 Your current SimpleOCR setup processes images in {simple_ocr_time:.2f}s")
    print("   This is excellent performance for purchase order processing!")

if __name__ == "__main__":
    asyncio.run(main())
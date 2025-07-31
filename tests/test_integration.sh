#!/bin/bash

# Test script for OCR MCP Server integration
echo "🧪 Testing OCR MCP Server Integration"
echo "=================================="

# Test 1: Check OCR CLI
echo "1. Testing OCR CLI..."
cd /Users/macbookpro/odoo-mcp-server
/Users/macbookpro/odoo-mcp-server/ocr-env/bin/python ocr_cli.py --single "/Users/macbookpro/Documents/Odoo MCP/purchase/IMG_2444.jpeg" > /tmp/ocr_test.json 2>/dev/null

if [ $? -eq 0 ]; then
    echo "   ✅ OCR CLI works"
    # Check if we got valid JSON
    python3 -m json.tool /tmp/ocr_test.json > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "   ✅ JSON output is valid"
    else
        echo "   ❌ JSON output is invalid"
    fi
else
    echo "   ❌ OCR CLI failed"
fi

# Test 2: Check MCP server files
echo "2. Checking MCP server files..."
if [ -f "ocr-mcp-server.js" ]; then
    echo "   ✅ OCR MCP server file exists"
else
    echo "   ❌ OCR MCP server file missing"
fi

if [ -f "ocr_cli.py" ]; then
    echo "   ✅ OCR CLI script exists"
else
    echo "   ❌ OCR CLI script missing"
fi

# Test 3: Check Python environment
echo "3. Checking Python environment..."
if [ -f "ocr-env/bin/python" ]; then
    echo "   ✅ Python virtual environment exists"
    /Users/macbookpro/odoo-mcp-server/ocr-env/bin/python -c "import easyocr; print('   ✅ EasyOCR is available')" 2>/dev/null || echo "   ❌ EasyOCR not available"
else
    echo "   ❌ Python virtual environment missing"
fi

# Test 4: Check purchase folder
echo "4. Checking purchase folder..."
if [ -d "/Users/macbookpro/Documents/Odoo MCP/purchase" ]; then
    image_count=$(find "/Users/macbookpro/Documents/Odoo MCP/purchase" -name "*.jpeg" -o -name "*.jpg" -o -name "*.png" | wc -l)
    echo "   ✅ Purchase folder exists with $image_count image files"
else
    echo "   ❌ Purchase folder not found"
fi

# Test 5: Check Claude Desktop config
echo "5. Checking Claude Desktop configuration..."
if [ -f "/Users/macbookpro/Library/Application Support/Claude/claude_desktop_config.json" ]; then
    echo "   ✅ Claude Desktop config exists"
    if grep -q "ocr-mcp-server.js" "/Users/macbookpro/Library/Application Support/Claude/claude_desktop_config.json"; then
        echo "   ✅ OCR server is configured in Claude Desktop"
    else
        echo "   ❌ OCR server not found in Claude Desktop config"
    fi
else
    echo "   ❌ Claude Desktop config not found"
fi

echo ""
echo "🎯 Integration test complete!"
echo ""
echo "Next steps:"
echo "1. Restart Claude Desktop to load the new OCR server"
echo "2. Test the OCR tools in Claude Desktop"
echo "3. Process some purchase order images"
echo ""
# OCR MCP Server Integration Guide

## Overview
This integration provides OCR (Optical Character Recognition) capabilities alongside your existing Odoo MCP server, allowing Claude Desktop to extract structured data from purchase order images, invoices, and other documents.

## Components

### 1. OCR MCP Server (`ocr-mcp-server.js`)
A Node.js MCP server that provides OCR tools for Claude Desktop:
- `process_image_ocr` - Extract text from single images
- `process_purchase_order` - Extract structured purchase order data
- `batch_process_purchase_folder` - Process multiple images at once
- `list_purchase_images` - List available images
- `get_ocr_status` - Check system status

### 2. OCR CLI Script (`ocr_cli.py`)
Python command-line interface that handles the actual OCR processing using EasyOCR.

### 3. Simple OCR Library (`simple_ocr.py`)
Core OCR processing library with caching, image preprocessing, and structured data extraction.

## Installation Status
✅ All components are installed and configured
✅ Python virtual environment with EasyOCR is ready
✅ Claude Desktop configuration is updated
✅ Purchase folder with sample images is available

## Available Tools in Claude Desktop

### Basic OCR
```
process_image_ocr
```
- Extract text from any image file
- Optional structured data extraction for purchase orders
- Returns full OCR results with confidence scores

### Purchase Order Processing
```
process_purchase_order
```
- Specifically designed for purchase orders and invoices
- Extracts: PO numbers, vendor names, dates, amounts, line items
- Returns structured business data

### Batch Processing
```
batch_process_purchase_folder
```
- Process multiple images at once
- Default folder: `/Users/macbookpro/Documents/Odoo MCP/purchase`
- Configurable file limit for performance

### Utility Tools
```
list_purchase_images
get_ocr_status
```

## Usage Examples

### Process a Single Purchase Order
```
Use the process_purchase_order tool with:
file_path: "/Users/macbookpro/Documents/Odoo MCP/purchase/IMG_2444.jpeg"
```

### Batch Process All Purchase Images
```
Use batch_process_purchase_folder with:
limit: 5
```

### Check System Status
```
Use get_ocr_status (no parameters needed)
```

## Extracted Data Structure

For purchase orders, the system extracts:
- **Document Type**: Purchase Order, Invoice, etc.
- **PO Number**: Purchase order reference number
- **Vendor Details**: Company name, contact information
- **Financial Data**: Total amounts, line items
- **Dates**: Order dates, delivery dates
- **Line Items**: Product descriptions, quantities, prices

## File Locations

- **OCR Server**: `/Users/macbookpro/odoo-mcp-server/ocr-mcp-server.js`
- **Python Environment**: `/Users/macbookpro/odoo-mcp-server/ocr-env/`
- **Purchase Images**: `/Users/macbookpro/Documents/Odoo MCP/purchase/`
- **Cache Directory**: `/Users/macbookpro/odoo-mcp-server/ocr_cache/`
- **Claude Config**: `/Users/macbookpro/Library/Application Support/Claude/claude_desktop_config.json`

## Performance Notes

- **Caching**: OCR results are cached to avoid reprocessing the same images
- **GPU Support**: Currently using CPU mode (set gpu=True in simple_ocr.py if CUDA available)
- **Image Preprocessing**: Automatic image optimization for better OCR accuracy
- **Batch Processing**: More efficient for multiple files

## Testing

Run the integration test:
```bash
cd /Users/macbookpro/odoo-mcp-server
./test_integration.sh
```

## Next Steps

1. **Restart Claude Desktop** to load the new OCR server
2. **Test OCR tools** with your purchase order images
3. **Process real data** and verify extraction accuracy
4. **Integrate with Odoo** using both servers together

## Troubleshooting

### Common Issues

1. **"OCR process failed"**
   - Check that the Python virtual environment is activated
   - Verify EasyOCR is installed: `ocr-env/bin/python -c "import easyocr"`

2. **"File not found"**
   - Ensure image files exist in the purchase folder
   - Check file paths are absolute, not relative

3. **"JSON serialization errors"**
   - Fixed in current version with NumpyEncoder
   - Debug messages now go to stderr, not stdout

4. **Poor OCR accuracy**
   - Images may need better quality or resolution
   - Check image preprocessing settings in simple_ocr.py

### Server Configuration

Both servers are configured in Claude Desktop:
```json
{
  "mcpServers": {
    "odoo": {
      "command": "node",
      "args": ["/Users/macbookpro/odoo-mcp-server/odoo-mcp-server.js"]
    },
    "ocr": {
      "command": "node", 
      "args": ["/Users/macbookpro/odoo-mcp-server/ocr-mcp-server.js"],
      "cwd": "/Users/macbookpro/odoo-mcp-server"
    }
  }
}
```

## Integration with Odoo

You can now use both servers together:
1. Use OCR tools to extract data from purchase order images
2. Use Odoo tools to create/update records based on extracted data
3. Automate the entire purchase order processing workflow

The OCR server provides the extracted data, while the Odoo server handles the ERP operations.
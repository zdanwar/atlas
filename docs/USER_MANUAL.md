# 📚 MCP Tools User Manual - Simple Guide for Everyone

## 🎯 What is This System?

Think of this system as your **digital assistant** that can:
- 📷 Read text from photos and PDFs (like invoices, purchase orders)
- 📊 Convert that information into Excel files
- 🏢 Connect to your Odoo business system
- 📁 Manage files on your computer
- 🤖 Do all of this automatically with simple commands!

---

## 🚀 Quick Start Guide

### Step 1: Make Sure Everything is Ready
When you open Claude Desktop, you should see these tools available:
- **Filesystem** - Works with files on your computer
- **Odoo** - Connects to your business system
- **OCR** - Reads text from images and PDFs
- **Excel** - Creates and edits spreadsheets

### Step 2: Your First Commands

Here are the most useful commands you can type:

#### 📷 To Read Text from an Image or PDF:
```
Process the invoice image: /Users/macbookpro/Documents/Odoo MCP/purchase/invoice.jpg
```

#### 📑 To Process Multiple Documents at Once:
```
Process all purchase orders in my purchase folder
```

#### 🔍 To Search in Odoo:
```
Find all customers with email addresses
Show me recent sales orders
```

#### 📊 To Create Excel Files:
```
Create an Excel file with the extracted invoice data
```

---

## 📖 Detailed Guide for Each Tool

### 1. 📁 File Management (Filesystem Tool)

**What it does:** Helps you work with files and folders on your computer.

**Common Uses:**
- List files in a folder
- Read contents of a file
- Create new files
- Search for specific files

**Example Commands:**
- "Show me all files in my Documents folder"
- "Read the contents of invoice.txt"
- "Create a new folder called 'Processed Invoices'"

### 2. 📷 Document Reading (OCR Tool)

**What it does:** Reads text from images and PDFs, even handwritten or scanned documents.

**Supported File Types:**
- 📸 Photos (JPEG, PNG, HEIF from iPhone)
- 📄 PDF documents
- 🖼️ Scanned documents

**Example Commands:**
- "Extract text from this invoice photo"
- "Read all purchase orders in my folder"
- "Get the invoice number and total amount from this PDF"

**Special Features:**
- Automatically finds invoice numbers, dates, amounts
- Works with photos taken from your phone
- Can process multiple files at once

### 3. 🏢 Business System (Odoo Tool)

**What it does:** Connects to your Odoo business system to search and retrieve information.

**What You Can Search:**
- 👥 Customers and contacts
- 📦 Products
- 💰 Sales orders and invoices
- 📊 Financial information
- 👤 Users and companies

**Example Commands:**
- "Find customer John Smith"
- "Show me all products under $100"
- "Get sales orders from last month"
- "Show financial summary"

### 4. 📊 Spreadsheet Creation (Excel Tool)

**What it does:** Creates and modifies Excel files.

**Common Uses:**
- Create import templates for Odoo
- Export extracted data to Excel
- Format data for easy reading

**Example Commands:**
- "Create an Excel file with customer data"
- "Export invoice data to spreadsheet"

---

## 🔄 Common Workflows

### Workflow 1: Process Invoices to Excel
1. **Take a photo** of your invoice with your phone
2. **Save it** to the purchase folder
3. **Tell Claude:** "Process the new invoice photo and create an Excel file"
4. **Result:** Excel file ready for Odoo import!

### Workflow 2: Batch Process Purchase Orders
1. **Put all PO images** in your purchase folder
2. **Tell Claude:** "Process all purchase orders and extract key data"
3. **Review** the extracted information
4. **Export** to Excel for import

### Workflow 3: Search and Export from Odoo
1. **Search:** "Find all customers from California"
2. **Export:** "Create an Excel file with these customers"
3. **Use** the Excel file for analysis or updates

---

## 💡 Tips and Tricks

### For Better OCR Results:
- 📸 Take clear, well-lit photos
- 📐 Keep documents straight (not angled)
- 🔍 Make sure text is in focus
- 📱 iPhone photos work great!

### For Faster Processing:
- 🗂️ Organize files in folders by type
- 🏷️ Use consistent naming (invoice_001.jpg, invoice_002.jpg)
- 🔄 Process similar documents together
- 💾 Files are cached - processing the same file twice is instant!

### Common Patterns the System Recognizes:
- **Invoice Numbers:** INV-12345, Invoice #12345
- **PO Numbers:** PO-12345, Purchase Order 12345
- **Amounts:** $1,234.56, Total: 1,234.56
- **Dates:** 01/15/2024, January 15, 2024
- **Emails:** contact@company.com
- **Phone:** (555) 123-4567

---

## 🛠️ Troubleshooting

### "File not found" Error
- ✅ Check the file path is correct
- ✅ Make sure the file exists
- ✅ Use the full path starting with /Users/

### "Cannot read image" Error
- ✅ Make sure the image isn't corrupted
- ✅ Try opening it in Preview first
- ✅ Check if it's a supported format

### "Odoo connection failed"
- ✅ Check your internet connection
- ✅ Verify Odoo is accessible
- ✅ Contact your administrator

### OCR gives poor results
- ✅ Image quality might be too low
- ✅ Try taking a new photo with better lighting
- ✅ Make sure text is clearly visible

---

## 📋 Quick Reference Card

### Essential Commands

| What You Want | What to Say |
|--------------|-------------|
| Read an invoice | "Process invoice.jpg from purchase folder" |
| Read a PDF | "Extract text from document.pdf" |
| Process multiple files | "Process all images in purchase folder" |
| Search customers | "Find customers named Smith" |
| Search products | "Show products under $50" |
| Get sales data | "Show recent sales orders" |
| Create Excel | "Create Excel with extracted data" |
| List files | "Show files in Documents folder" |

### File Locations

| Type | Location |
|------|----------|
| Purchase Orders | `/Users/macbookpro/Documents/Odoo MCP/purchase/` |
| Documents | `/Users/macbookpro/Documents/Odoo MCP/` |
| Processed Files | Check the same folder - look for .json or .xlsx files |

---

## 🎯 Business Use Cases

### For Accounting:
1. **Invoice Processing:** Photo → Text → Excel → Odoo Import
2. **Expense Reports:** Scan receipts → Extract amounts → Create summary
3. **Vendor Bills:** PDF → Extract data → Match with POs

### For Purchasing:
1. **PO Processing:** Scan POs → Extract items → Create orders
2. **Price Comparisons:** Extract prices from quotes → Compare in Excel
3. **Vendor Database:** Extract contact info → Update Odoo

### For Sales:
1. **Order Entry:** Customer PO → Extract → Create sales order
2. **Customer Database:** Business cards → Extract → Add to Odoo
3. **Quote Management:** PDF quotes → Extract → Track in system

---

## 🔒 Security & Privacy

- ✅ Your data stays on your computer
- ✅ Odoo connection is encrypted
- ✅ No data is sent to external services
- ✅ Processed files are cached locally

---

## 📞 Getting Help

### If you need help:
1. **Check this manual** for your task
2. **Try the examples** provided
3. **Ask Claude** to explain what went wrong
4. **Contact support** with the error message

### Useful questions to ask Claude:
- "What OCR tools are available?"
- "Show me an example of processing an invoice"
- "How do I search for products in Odoo?"
- "Can you check if my OCR system is working?"

---

## 🚀 Advanced Features (Coming Soon)

### Phase 1 - Current
- ✅ Read documents (OCR)
- ✅ Search Odoo
- ✅ Create Excel files
- ✅ Basic automation

### Phase 2 - Next
- 🔄 Auto-process new files
- 📊 Smart data mapping
- 🤖 Batch operations
- 📧 Email integration

### Phase 3 - Future
- 🔌 Direct Odoo import
- 📱 Mobile app
- 🌐 Web interface
- 🤝 Multi-user support

---

## 🎉 You're Ready!

You now know how to:
- Extract text from any document
- Search your Odoo system
- Create Excel files for import
- Automate repetitive tasks

Start with simple commands and work your way up. The system is designed to help you, and Claude is always there to guide you!

**Remember:** You don't need to be technical - just describe what you want to do in plain English!

---

*Last updated: January 2025*
*Version: 1.0*
#!/usr/bin/env node

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { 
    CallToolRequestSchema,
    ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Path to the Python OCR environment and script  
const PYTHON_ENV = '/usr/local/bin/python3'; // Use system Python with installed packages
const OCR_SCRIPT = path.join(__dirname, 'ocr_cli.py');
const PURCHASE_FOLDER = '/Users/macbookpro/Documents/Odoo MCP/purchase';

// Helper function to run Python OCR script
function runOCRScript(filePath, operation = 'image', documentType = 'purchase_order') {
    return new Promise((resolve, reject) => {
        const args = operation === 'batch' ? 
            [OCR_SCRIPT, 'batch', filePath, '--document-type', documentType] : 
            operation === 'pdf' ?
            [OCR_SCRIPT, 'pdf', filePath, '--document-type', documentType] :
            [OCR_SCRIPT, 'image', filePath, '--document-type', documentType];
            
        const pythonProcess = spawn(PYTHON_ENV, args, {
            cwd: __dirname,
            stdio: ['pipe', 'pipe', 'pipe']
        });

        let stdout = '';
        let stderr = '';

        pythonProcess.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        pythonProcess.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        pythonProcess.on('close', (code) => {
            if (code === 0) {
                try {
                    const result = JSON.parse(stdout);
                    resolve(result);
                } catch (parseError) {
                    resolve({ success: false, error: 'Failed to parse OCR output', raw_output: stdout });
                }
            } else {
                reject(new Error(`OCR process failed with code ${code}: ${stderr}`));
            }
        });

        pythonProcess.on('error', (error) => {
            reject(new Error(`Failed to start OCR process: ${error.message}`));
        });
    });
}

// Helper function to extract purchase order structured data
function extractPurchaseOrderData(ocrResult) {
    if (!ocrResult.success) {
        return { success: false, error: ocrResult.error };
    }

    const fullText = ocrResult.combined.full_text.toLowerCase();
    const textBlocks = ocrResult.combined.text_blocks;
    
    // Initialize extraction results
    const extractedData = {
        document_type: null,
        po_number: null,
        vendor_name: null,
        date: null,
        total_amount: null,
        items: [],
        vendor_details: {
            address: null,
            phone: null,
            email: null
        },
        buyer_details: {
            company: null,
            address: null
        }
    };

    // Detect document type
    if (fullText.includes('purchase order') || fullText.includes('po no') || fullText.includes('p.o.')) {
        extractedData.document_type = 'Purchase Order';
    } else if (fullText.includes('invoice') || fullText.includes('bill')) {
        extractedData.document_type = 'Invoice';
    }

    // Extract PO Number
    const poPatterns = [
        /po\s*no\.?\s*:?\s*([A-Za-z0-9\-\/]+)/i,
        /purchase\s*order\s*no\.?\s*:?\s*([A-Za-z0-9\-\/]+)/i,
        /p\.o\.?\s*no\.?\s*:?\s*([A-Za-z0-9\-\/]+)/i
    ];
    
    for (const pattern of poPatterns) {
        const match = fullText.match(pattern);
        if (match) {
            extractedData.po_number = match[1].trim().toUpperCase();
            break;
        }
    }

    // Extract dates
    const datePatterns = [
        /(\d{1,2}[-\/\.]\d{1,2}[-\/\.]\d{2,4})/g,
        /(\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{2,4})/gi
    ];
    
    const dates = [];
    for (const pattern of datePatterns) {
        const matches = fullText.match(pattern);
        if (matches) {
            dates.push(...matches);
        }
    }
    if (dates.length > 0) {
        extractedData.date = dates[0];
    }

    // Extract amounts (look for currency symbols and numbers)
    const amountPatterns = [
        /(?:total|amount|sum)[\s:]*(?:rs\.?|₹|\$)?\s*([0-9,]+\.?\d*)/gi,
        /(?:rs\.?|₹|\$)\s*([0-9,]+\.?\d*)/g
    ];
    
    const amounts = [];
    for (const pattern of amountPatterns) {
        const matches = fullText.match(pattern);
        if (matches) {
            amounts.push(...matches.map(m => m.replace(/[^\d.,]/g, '')));
        }
    }
    if (amounts.length > 0) {
        extractedData.total_amount = amounts[amounts.length - 1]; // Usually the last/largest amount is total
    }

    // Extract vendor name (usually at the top of the document)
    const topRows = ocrResult.combined.rows.slice(0, 5);
    for (const row of topRows) {
        const rowText = row.map(item => item.text).join(' ');
        if (rowText.length > 5 && !rowText.toLowerCase().includes('purchase') && 
            !rowText.toLowerCase().includes('order') && !rowText.toLowerCase().includes('po no')) {
            if (extractedData.vendor_name === null || rowText.length > extractedData.vendor_name.length) {
                extractedData.vendor_name = rowText.trim();
            }
        }
    }

    // Extract line items (look for patterns in rows)
    const itemRows = [];
    for (const row of ocrResult.combined.rows) {
        const rowText = row.map(item => item.text).join(' ').toLowerCase();
        // Look for rows that might contain items (have quantities, descriptions, amounts)
        if (rowText.match(/\d+/) && rowText.length > 10 && 
            !rowText.includes('po no') && !rowText.includes('date') && 
            !rowText.includes('total')) {
            itemRows.push({
                text: row.map(item => item.text).join(' | '),
                raw_row: row
            });
        }
    }
    
    extractedData.items = itemRows.slice(0, 20); // Limit to first 20 potential items

    // Try to find contact details
    const emailPattern = /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g;
    const phonePattern = /(\+?\d{1,4}[\s-]?\(?\d{1,4}\)?[\s-]?\d{1,4}[\s-]?\d{1,9})/g;
    
    const emails = fullText.match(emailPattern);
    const phones = fullText.match(phonePattern);
    
    if (emails) extractedData.vendor_details.email = emails[0];
    if (phones) extractedData.vendor_details.phone = phones[0];

    return {
        success: true,
        extracted_data: extractedData,
        confidence_score: ocrResult.combined.avg_confidence,
        total_text_blocks: ocrResult.combined.total_text_blocks
    };
}

// Create the MCP server
const server = new Server(
    {
        name: 'ocr-server',
        version: '1.0.0',
    },
    {
        capabilities: {
            tools: {},
        },
    }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: 'process_image_ocr',
                description: 'Extract text from a single image file using OCR',
                inputSchema: {
                    type: 'object',
                    properties: {
                        file_path: { 
                            type: 'string', 
                            description: 'Absolute path to the image file to process' 
                        },
                        extract_structured_data: {
                            type: 'boolean',
                            description: 'Whether to extract structured purchase order data (default: false)',
                            default: false
                        }
                    },
                    required: ['file_path']
                }
            },
            {
                name: 'process_purchase_order',
                description: 'Extract structured data from purchase order images (invoices, POs)',
                inputSchema: {
                    type: 'object',
                    properties: {
                        file_path: { 
                            type: 'string', 
                            description: 'Absolute path to the purchase order image file' 
                        }
                    },
                    required: ['file_path']
                }
            },
            {
                name: 'batch_process_purchase_folder',
                description: 'Process all images in the purchase folder and extract structured data',
                inputSchema: {
                    type: 'object',
                    properties: {
                        folder_path: {
                            type: 'string',
                            description: 'Path to folder containing purchase order images',
                            default: PURCHASE_FOLDER
                        },
                        limit: {
                            type: 'number',
                            description: 'Maximum number of files to process',
                            default: 10
                        }
                    }
                }
            },
            {
                name: 'list_purchase_images',
                description: 'List all image files in the purchase folder',
                inputSchema: {
                    type: 'object',
                    properties: {
                        folder_path: {
                            type: 'string',
                            description: 'Path to folder containing images',
                            default: PURCHASE_FOLDER
                        }
                    }
                }
            },
            {
                name: 'get_ocr_status',
                description: 'Check OCR system status and environment',
                inputSchema: {
                    type: 'object',
                    properties: {}
                }
            },
            {
                name: 'process_pdf_advanced',
                description: 'Process PDF with advanced hybrid text extraction and OCR',
                inputSchema: {
                    type: 'object',
                    properties: {
                        file_path: { 
                            type: 'string', 
                            description: 'Absolute path to the PDF file' 
                        },
                        max_pages: {
                            type: 'number',
                            description: 'Maximum number of pages to process (default: 20)',
                            default: 20
                        },
                        extract_tables: {
                            type: 'boolean',
                            description: 'Attempt to extract tables from PDF (default: false)',
                            default: false
                        }
                    },
                    required: ['file_path']
                }
            },
            {
                name: 'analyze_pdf',
                description: 'Analyze PDF to determine content type and processing strategy',
                inputSchema: {
                    type: 'object',
                    properties: {
                        file_path: { 
                            type: 'string', 
                            description: 'Absolute path to the PDF file' 
                        }
                    },
                    required: ['file_path']
                }
            }
        ],
    };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
        switch (name) {
            case 'process_image_ocr':
                if (!fs.existsSync(args.file_path)) {
                    throw new Error(`File not found: ${args.file_path}`);
                }

                const ocrResult = await runOCRScript(args.file_path, 'single');
                
                let response = {
                    content: [{
                        type: 'text',
                        text: `OCR Results for: ${path.basename(args.file_path)}\n\n`
                    }]
                };

                if (ocrResult.success) {
                    let output = `✅ Successfully processed ${ocrResult.file_name}\n`;
                    output += `📊 Extracted ${ocrResult.combined.total_text_blocks} text blocks\n`;
                    output += `🎯 Average confidence: ${ocrResult.combined.avg_confidence}\n\n`;
                    
                    if (args.extract_structured_data) {
                        const structuredData = extractPurchaseOrderData(ocrResult);
                        if (structuredData.success) {
                            output += `📋 Structured Data:\n`;
                            output += `• Document Type: ${structuredData.extracted_data.document_type || 'Unknown'}\n`;
                            output += `• PO Number: ${structuredData.extracted_data.po_number || 'Not found'}\n`;
                            output += `• Vendor: ${structuredData.extracted_data.vendor_name || 'Not found'}\n`;
                            output += `• Date: ${structuredData.extracted_data.date || 'Not found'}\n`;
                            output += `• Total Amount: ${structuredData.extracted_data.total_amount || 'Not found'}\n\n`;
                        }
                    }
                    
                    output += `📝 Full Text:\n${ocrResult.combined.full_text}`;
                    
                    response.content[0].text += output;
                } else {
                    response.content[0].text += `❌ OCR failed: ${ocrResult.error}`;
                }

                return response;

            case 'process_purchase_order':
                if (!fs.existsSync(args.file_path)) {
                    throw new Error(`File not found: ${args.file_path}`);
                }

                const poOcrResult = await runOCRScript(args.file_path, 'single');
                const structuredData = extractPurchaseOrderData(poOcrResult);

                if (structuredData.success) {
                    const data = structuredData.extracted_data;
                    let output = `📋 Purchase Order Analysis: ${path.basename(args.file_path)}\n\n`;
                    
                    output += `🏷️  Document Type: ${data.document_type || 'Unknown'}\n`;
                    output += `📄 PO Number: ${data.po_number || 'Not detected'}\n`;
                    output += `🏢 Vendor: ${data.vendor_name || 'Not detected'}\n`;
                    output += `📅 Date: ${data.date || 'Not detected'}\n`;
                    output += `💰 Total Amount: ${data.total_amount || 'Not detected'}\n\n`;
                    
                    if (data.vendor_details.email || data.vendor_details.phone) {
                        output += `📞 Vendor Contact:\n`;
                        if (data.vendor_details.email) output += `• Email: ${data.vendor_details.email}\n`;
                        if (data.vendor_details.phone) output += `• Phone: ${data.vendor_details.phone}\n`;
                        output += '\n';
                    }
                    
                    if (data.items.length > 0) {
                        output += `📦 Detected Items (${data.items.length}):\n`;
                        data.items.slice(0, 5).forEach((item, index) => {
                            output += `${index + 1}. ${item.text}\n`;
                        });
                        if (data.items.length > 5) {
                            output += `... and ${data.items.length - 5} more items\n`;
                        }
                        output += '\n';
                    }
                    
                    output += `🎯 OCR Confidence: ${structuredData.confidence_score}\n`;
                    output += `📊 Text Blocks Processed: ${structuredData.total_text_blocks}`;

                    return {
                        content: [{
                            type: 'text',
                            text: output
                        }]
                    };
                } else {
                    return {
                        content: [{
                            type: 'text',
                            text: `❌ Failed to process purchase order: ${structuredData.error}`
                        }]
                    };
                }

            case 'batch_process_purchase_folder':
                const folderPath = args.folder_path || PURCHASE_FOLDER;
                
                if (!fs.existsSync(folderPath)) {
                    throw new Error(`Folder not found: ${folderPath}`);
                }

                const files = fs.readdirSync(folderPath)
                    .filter(file => /\.(jpg|jpeg|png|pdf)$/i.test(file))
                    .slice(0, args.limit || 10);

                if (files.length === 0) {
                    return {
                        content: [{
                            type: 'text',
                            text: '📁 No image files found in the purchase folder.'
                        }]
                    };
                }

                let batchOutput = `🚀 Processing ${files.length} purchase order files...\n\n`;
                const results = [];

                // Use batch processing for efficiency
                const batchResult = await runOCRScript(folderPath, 'batch', args.limit || 10);
                
                if (batchResult.success) {
                    for (const ocrResult of batchResult.results) {
                        const fileName = path.basename(ocrResult.file_path || ocrResult.file_name || 'unknown');
                        batchOutput += `📄 Processing: ${fileName}\n`;
                        
                        if (ocrResult.success) {
                            const structured = extractPurchaseOrderData(ocrResult);
                            
                            if (structured.success) {
                                const data = structured.extracted_data;
                                batchOutput += `  ✅ Success - PO: ${data.po_number || 'N/A'}, Vendor: ${data.vendor_name || 'N/A'}\n`;
                                results.push({
                                    file: fileName,
                                    success: true,
                                    po_number: data.po_number,
                                    vendor: data.vendor_name,
                                    amount: data.total_amount
                                });
                            } else {
                                batchOutput += `  ❌ Failed to extract structured data\n`;
                                results.push({
                                    file: fileName,
                                    success: false,
                                    error: structured.error
                                });
                            }
                        } else {
                            batchOutput += `  ❌ OCR Error: ${ocrResult.error}\n`;
                            results.push({
                                file: fileName,
                                success: false,
                                error: ocrResult.error
                            });
                        }
                    }
                } else {
                    throw new Error(batchResult.error);
                }

                const successful = results.filter(r => r.success);
                batchOutput += `\n📊 Summary: ${successful.length}/${files.length} files processed successfully\n\n`;
                
                if (successful.length > 0) {
                    batchOutput += `✅ Successfully Processed:\n`;
                    successful.forEach(result => {
                        batchOutput += `• ${result.file}: PO ${result.po_number || 'N/A'} - ${result.vendor || 'Unknown vendor'}\n`;
                    });
                }

                return {
                    content: [{
                        type: 'text',
                        text: batchOutput
                    }]
                };

            case 'list_purchase_images':
                const listFolderPath = args.folder_path || PURCHASE_FOLDER;
                
                if (!fs.existsSync(listFolderPath)) {
                    throw new Error(`Folder not found: ${listFolderPath}`);
                }

                const imageFiles = fs.readdirSync(listFolderPath)
                    .filter(file => /\.(jpg|jpeg|png|pdf)$/i.test(file))
                    .map(file => {
                        const filePath = path.join(listFolderPath, file);
                        const stats = fs.statSync(filePath);
                        return {
                            name: file,
                            size: (stats.size / 1024).toFixed(1) + ' KB',
                            modified: stats.mtime.toISOString().split('T')[0]
                        };
                    });

                let listOutput = `📁 Purchase Images in ${listFolderPath}\n\n`;
                listOutput += `Found ${imageFiles.length} image files:\n\n`;

                imageFiles.forEach((file, index) => {
                    listOutput += `${index + 1}. ${file.name}\n`;
                    listOutput += `   Size: ${file.size}, Modified: ${file.modified}\n\n`;
                });

                return {
                    content: [{
                        type: 'text',
                        text: listOutput
                    }]
                };

            case 'get_ocr_status':
                let statusOutput = `🔍 OCR System Status\n\n`;
                
                // Check Python environment
                const pythonExists = fs.existsSync(PYTHON_ENV);
                statusOutput += `🐍 Python Environment: ${pythonExists ? '✅ Found' : '❌ Not found'} (${PYTHON_ENV})\n`;
                
                // Check OCR script
                const scriptExists = fs.existsSync(OCR_SCRIPT);
                statusOutput += `📝 OCR Script: ${scriptExists ? '✅ Found' : '❌ Not found'} (${OCR_SCRIPT})\n`;
                
                // Check purchase folder
                const folderExists = fs.existsSync(PURCHASE_FOLDER);
                statusOutput += `📁 Purchase Folder: ${folderExists ? '✅ Found' : '❌ Not found'} (${PURCHASE_FOLDER})\n`;
                
                if (folderExists) {
                    const imageCount = fs.readdirSync(PURCHASE_FOLDER)
                        .filter(file => /\.(jpg|jpeg|png|pdf)$/i.test(file)).length;
                    statusOutput += `📷 Images Available: ${imageCount}\n`;
                }
                
                statusOutput += `\n🔧 System Ready: ${pythonExists && scriptExists ? '✅ Yes' : '❌ No'}`;

                return {
                    content: [{
                        type: 'text',
                        text: statusOutput
                    }]
                };

            case 'process_pdf_advanced':
                if (!fs.existsSync(args.file_path)) {
                    throw new Error(`PDF file not found: ${args.file_path}`);
                }

                const pdfOcrResult = await runOCRScript(args.file_path, 'single');
                
                if (pdfOcrResult.success) {
                    let output = `📄 Advanced PDF Processing: ${path.basename(args.file_path)}\n\n`;
                    
                    // PDF Analysis info
                    if (pdfOcrResult.pdf_analysis) {
                        const analysis = pdfOcrResult.pdf_analysis;
                        output += `📊 PDF Analysis:\n`;
                        output += `• File Size: ${analysis.file_size_mb?.toFixed(1) || 'N/A'} MB\n`;
                        output += `• Total Pages: ${analysis.page_count || 'N/A'}\n`;
                        output += `• Content Type: ${analysis.is_text_based ? 'Text-based' : analysis.is_image_based ? 'Image-based' : 'Hybrid'}\n`;
                        output += `• Processing Method: ${pdfOcrResult.processing_method || 'OCR'}\n\n`;
                    }
                    
                    // Structured data extraction
                    if (pdfOcrResult.structured_data) {
                        const data = pdfOcrResult.structured_data;
                        output += `📋 Extracted Data:\n`;
                        output += `• Document Type: ${data.document_type || 'Unknown'}\n`;
                        if (data.invoice_number) output += `• Invoice Number: ${data.invoice_number}\n`;
                        if (data.po_number) output += `• PO Number: ${data.po_number}\n`;
                        if (data.vendor_name) output += `• Vendor: ${data.vendor_name}\n`;
                        if (data.date) output += `• Date: ${data.date}\n`;
                        if (data.total_amount) output += `• Total Amount: ${data.total_amount}\n`;
                        
                        if (data.contact_info && (data.contact_info.email || data.contact_info.phone)) {
                            output += `\n📞 Contact Info:\n`;
                            if (data.contact_info.email) output += `• Email: ${data.contact_info.email}\n`;
                            if (data.contact_info.phone) output += `• Phone: ${data.contact_info.phone}\n`;
                        }
                        output += '\n';
                    }
                    
                    // Page processing summary
                    output += `📄 Pages Processed: ${pdfOcrResult.total_pages || 0}\n`;
                    if (pdfOcrResult.pages && pdfOcrResult.pages.length > 0) {
                        const textPages = pdfOcrResult.pages.filter(p => p.extraction_method === 'text').length;
                        const ocrPages = pdfOcrResult.pages.filter(p => p.extraction_method === 'ocr').length;
                        
                        if (textPages > 0) output += `• Text Extraction: ${textPages} pages\n`;
                        if (ocrPages > 0) output += `• OCR Processing: ${ocrPages} pages\n`;
                        
                        // Show confidence for OCR pages
                        const ocrConfidences = pdfOcrResult.pages
                            .filter(p => p.extraction_method === 'ocr' && p.avg_confidence)
                            .map(p => p.avg_confidence);
                        
                        if (ocrConfidences.length > 0) {
                            const avgConfidence = ocrConfidences.reduce((a, b) => a + b, 0) / ocrConfidences.length;
                            output += `• Average OCR Confidence: ${(avgConfidence * 100).toFixed(1)}%\n`;
                        }
                    }
                    
                    // Sample text
                    if (pdfOcrResult.combined && pdfOcrResult.combined.full_text) {
                        const sampleText = pdfOcrResult.combined.full_text.substring(0, 300);
                        output += `\n📝 Sample Text:\n${sampleText}${sampleText.length >= 300 ? '...' : ''}\n`;
                    }
                    
                    return {
                        content: [{
                            type: 'text',
                            text: output
                        }]
                    };
                } else {
                    return {
                        content: [{
                            type: 'text',
                            text: `❌ Failed to process PDF: ${pdfOcrResult.error || 'Unknown error'}`
                        }]
                    };
                }

            case 'analyze_pdf':
                if (!fs.existsSync(args.file_path)) {
                    throw new Error(`PDF file not found: ${args.file_path}`);
                }

                // Quick analysis without full processing
                const analysisResult = await runOCRScript(args.file_path, 'analyze');
                
                if (analysisResult.pdf_analysis) {
                    const analysis = analysisResult.pdf_analysis;
                    let output = `📊 PDF Analysis: ${path.basename(args.file_path)}\n\n`;
                    
                    output += `📁 File Information:\n`;
                    output += `• Size: ${analysis.file_size_mb?.toFixed(1) || 'N/A'} MB\n`;
                    output += `• Pages: ${analysis.page_count || 'N/A'}\n\n`;
                    
                    output += `📄 Content Type:\n`;
                    output += `• Text-based: ${analysis.is_text_based ? '✅ Yes' : '❌ No'}\n`;
                    output += `• Image-based: ${analysis.is_image_based ? '✅ Yes' : '❌ No'}\n`;
                    output += `• Hybrid: ${analysis.is_hybrid ? '✅ Yes' : '❌ No'}\n\n`;
                    
                    output += `🎯 Recommended Processing:\n`;
                    output += `• Strategy: ${analysis.recommended_strategy || 'OCR'}\n`;
                    
                    if (analysis.recommended_strategy === 'text_extraction') {
                        output += `• This PDF contains machine-readable text\n`;
                        output += `• Text extraction will be fast and 100% accurate\n`;
                    } else if (analysis.recommended_strategy === 'hybrid') {
                        output += `• This PDF contains both text and images\n`;
                        output += `• Hybrid processing will extract text where possible and OCR images\n`;
                    } else {
                        output += `• This PDF is primarily image-based\n`;
                        output += `• OCR will be used to extract text from images\n`;
                    }
                    
                    return {
                        content: [{
                            type: 'text',
                            text: output
                        }]
                    };
                } else {
                    return {
                        content: [{
                            type: 'text',
                            text: '❌ Could not analyze PDF file'
                        }]
                    };
                }

            default:
                throw new Error(`Unknown tool: ${name}`);
        }
    } catch (error) {
        return {
            content: [{
                type: 'text',
                text: `❌ Error: ${error.message}`
            }],
            isError: true,
        };
    }
});

// Start the server
async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error('OCR MCP server running on stdio');
}

main().catch(console.error);
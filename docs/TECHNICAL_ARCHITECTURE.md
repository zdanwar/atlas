# MCP Ecosystem Technical Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Components](#architecture-components)
3. [MCP Servers Detailed Specification](#mcp-servers-detailed-specification)
4. [Data Flow Architecture](#data-flow-architecture)
5. [Integration Architecture](#integration-architecture)
6. [Security Architecture](#security-architecture)
7. [Development Guidelines](#development-guidelines)
8. [API Reference](#api-reference)
9. [Deployment Architecture](#deployment-architecture)

---

## System Overview

### Architecture Philosophy
The MCP (Model Context Protocol) ecosystem is built on a microservices architecture pattern where each server provides specialized functionality that can be orchestrated together for complex workflows.

### Core Technology Stack
```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Desktop (Client)                   │
├─────────────────────────────────────────────────────────────┤
│                 MCP SDK (Protocol Layer)                     │
├──────────────┬──────────────┬──────────────┬───────────────┤
│  Filesystem  │     Odoo     │     OCR      │     Excel     │
│  MCP Server  │  MCP Server  │  MCP Server  │  MCP Server   │
├──────────────┴──────────────┴──────────────┴───────────────┤
│                    System Resources                          │
│  • File System  • Network  • Python Env  • Node.js Runtime  │
└─────────────────────────────────────────────────────────────┘
```

### Technology Choices
- **Protocol**: Model Context Protocol (MCP) via stdio
- **Runtime**: Node.js v18+ for MCP servers
- **OCR Backend**: Python 3.11 with EasyOCR, PyMuPDF, pdfplumber
- **GPU Acceleration**: Apple Metal Performance Shaders (MPS)
- **Database**: Odoo 17 (PostgreSQL backend)
- **Communication**: JSON-RPC 2.0 over HTTPS

---

## Architecture Components

### 1. MCP Server Infrastructure

#### Base Server Pattern
```javascript
class MCPServer {
    constructor(metadata, capabilities) {
        this.server = new Server(metadata, capabilities);
        this.transport = new StdioServerTransport();
    }
    
    async connect() {
        await this.server.connect(this.transport);
    }
    
    registerHandlers() {
        this.server.setRequestHandler(ListToolsRequestSchema, this.handleListTools);
        this.server.setRequestHandler(CallToolRequestSchema, this.handleCallTool);
    }
}
```

#### Communication Protocol
- **Transport**: stdio (standard input/output)
- **Format**: JSON-RPC 2.0
- **Message Flow**: Request → Server → Tool Execution → Response

### 2. Server Specifications

#### A. Filesystem MCP Server
- **Package**: `@modelcontextprotocol/server-filesystem`
- **Purpose**: File system operations within designated directory
- **Root Path**: `/Users/macbookpro/Documents/Odoo MCP`
- **Capabilities**: Read, Write, List, Search files

#### B. Odoo MCP Server
- **Location**: `/Users/macbookpro/odoo-mcp-server/odoo-mcp-server.js`
- **Connection**: HTTPS with SSL bypass for development
- **Authentication**: API key-based
- **Database**: `zdanwar-milestonealuminium-main-17798127`

#### C. OCR MCP Server
- **Location**: `/Users/macbookpro/odoo-mcp-server/ocr-mcp-server.js`
- **Backend**: Python subprocess via `ocr_cli.py`
- **Features**: 
  - GPU acceleration (AMD Radeon Pro 560X)
  - HEIF/HEIC support for iPhone images
  - Hybrid PDF processing
  - Caching system

#### D. Excel MCP Server
- **Package**: `@negokaz/excel-mcp-server`
- **Version**: 0.12.0
- **Cell Limit**: 4000 cells per operation
- **Format Support**: .xlsx, .xls

---

## MCP Servers Detailed Specification

### Odoo Server Tools

```typescript
interface OdooTools {
    // Search Operations
    search_partners(domain?: any[], limit?: number): Partner[]
    search_products(domain?: any[], limit?: number): Product[]
    search_sales_orders(domain?: any[], limit?: number): SaleOrder[]
    search_invoices(domain?: any[], limit?: number): Invoice[]
    search_stock_moves(domain?: any[], limit?: number): StockMove[]
    search_users(domain?: any[], limit?: number): User[]
    search_companies(domain?: any[], limit?: number): Company[]
    
    // Information Retrieval
    get_database_info(): DatabaseInfo
    get_chart_of_accounts(): Account[]
    get_financial_summary(): FinancialSummary
    get_module_status(): Module[]
}
```

### OCR Server Tools

```typescript
interface OCRTools {
    // Image Processing
    process_image_ocr(file_path: string, extract_structured_data?: boolean): OCRResult
    process_purchase_order(file_path: string): PurchaseOrderData
    
    // Batch Operations
    batch_process_purchase_folder(folder_path?: string, limit?: number): BatchResult
    
    // PDF Processing
    process_pdf_advanced(file_path: string, max_pages?: number): PDFResult
    analyze_pdf(file_path: string): PDFAnalysis
    
    // Utilities
    list_purchase_images(folder_path?: string): ImageFile[]
    get_ocr_status(): SystemStatus
}
```

### Data Models

```typescript
// Odoo Data Models
interface Partner {
    id: number
    name: string
    email?: string
    phone?: string
    is_company: boolean
    city?: string
    country_id?: [number, string]
}

interface Product {
    id: number
    name: string
    list_price: number
    standard_price: number
    qty_available: number
    categ_id?: [number, string]
}

// OCR Data Models
interface OCRResult {
    success: boolean
    file_path: string
    combined: {
        full_text: string
        text_blocks: TextBlock[]
        avg_confidence: number
    }
    structured_data?: ExtractedData
}

interface ExtractedData {
    document_type: string
    po_number?: string
    invoice_number?: string
    vendor_name?: string
    date?: string
    total_amount?: string
    line_items: LineItem[]
    contact_info: ContactInfo
}
```

---

## Data Flow Architecture

### Document Processing Pipeline

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│   Document  │────▶│     OCR      │────▶│  Structured   │────▶│    Excel     │
│   (Image/   │     │  Processing  │     │     Data      │     │  Generation  │
│    PDF)     │     │              │     │  Extraction   │     │              │
└─────────────┘     └──────────────┘     └───────────────┘     └──────────────┘
                            │                      │                      │
                            ▼                      ▼                      ▼
                    ┌──────────────┐     ┌───────────────┐     ┌──────────────┐
                    │   Caching    │     │  Validation   │     │    Odoo      │
                    │   System     │     │   & Mapping   │     │   Import     │
                    └──────────────┘     └───────────────┘     └──────────────┘
```

### Integration Flow

```python
# Example Integration Pipeline
async def process_purchase_document(file_path):
    # 1. Analyze document type
    analysis = await ocr_server.analyze_pdf(file_path)
    
    # 2. Extract data based on type
    if analysis.is_pdf:
        data = await ocr_server.process_pdf_advanced(file_path)
    else:
        data = await ocr_server.process_purchase_order(file_path)
    
    # 3. Map to Odoo structure
    odoo_data = map_to_odoo_format(data.structured_data)
    
    # 4. Generate Excel import file
    excel_path = await excel_server.create_import_template(odoo_data)
    
    # 5. Optional: Direct Odoo import
    if auto_import_enabled:
        result = await odoo_server.import_purchase_order(odoo_data)
    
    return {
        'extracted_data': data,
        'excel_file': excel_path,
        'odoo_result': result
    }
```

---

## Integration Architecture

### 1. MCP Server Orchestration

```javascript
class MCPOrchestrator {
    constructor() {
        this.servers = {
            filesystem: new FilesystemServer(),
            odoo: new OdooServer(),
            ocr: new OCRServer(),
            excel: new ExcelServer()
        };
    }
    
    async executeWorkflow(workflow) {
        const context = {};
        
        for (const step of workflow.steps) {
            const server = this.servers[step.server];
            const result = await server.execute(step.tool, step.params, context);
            context[step.id] = result;
        }
        
        return context;
    }
}
```

### 2. Event-Driven Architecture

```javascript
// Event Bus for inter-server communication
class MCPEventBus extends EventEmitter {
    async publish(event, data) {
        this.emit(event, data);
        await this.persistEvent(event, data);
    }
    
    subscribe(event, handler) {
        this.on(event, handler);
    }
}

// Usage
eventBus.subscribe('document.processed', async (data) => {
    await odooServer.createPurchaseOrder(data);
});
```

### 3. State Management

```javascript
class WorkflowState {
    constructor() {
        this.state = new Map();
        this.history = [];
    }
    
    setState(key, value) {
        this.state.set(key, value);
        this.history.push({ key, value, timestamp: Date.now() });
    }
    
    getState(key) {
        return this.state.get(key);
    }
    
    rollback(steps = 1) {
        // Implement rollback logic
    }
}
```

---

## Security Architecture

### 1. Authentication & Authorization

```javascript
// API Key Management
class APIKeyManager {
    constructor() {
        this.keys = new Map();
        this.permissions = new Map();
    }
    
    validateKey(key, requiredPermission) {
        const keyData = this.keys.get(key);
        if (!keyData || keyData.expired) return false;
        
        const permissions = this.permissions.get(key);
        return permissions.includes(requiredPermission);
    }
}
```

### 2. Data Encryption

```javascript
// Sensitive data handling
class SecureDataHandler {
    encrypt(data) {
        // Use Node.js crypto for encryption
        const cipher = crypto.createCipher('aes-256-cbc', process.env.ENCRYPTION_KEY);
        return cipher.update(JSON.stringify(data), 'utf8', 'hex') + cipher.final('hex');
    }
    
    decrypt(encryptedData) {
        const decipher = crypto.createDecipher('aes-256-cbc', process.env.ENCRYPTION_KEY);
        return JSON.parse(
            decipher.update(encryptedData, 'hex', 'utf8') + decipher.final('utf8')
        );
    }
}
```

### 3. Audit Logging

```javascript
class AuditLogger {
    async log(action, user, data) {
        const entry = {
            timestamp: new Date().toISOString(),
            action,
            user,
            data: this.sanitizeData(data),
            hash: this.generateHash(action, user, data)
        };
        
        await this.persistLog(entry);
    }
    
    sanitizeData(data) {
        // Remove sensitive information
        const sanitized = { ...data };
        delete sanitized.password;
        delete sanitized.apiKey;
        return sanitized;
    }
}
```

---

## Development Guidelines

### 1. Code Structure

```
odoo-mcp-ecosystem/
├── servers/
│   ├── odoo/
│   │   ├── src/
│   │   ├── tools/
│   │   └── tests/
│   ├── ocr/
│   │   ├── src/
│   │   ├── python/
│   │   └── tests/
│   └── integration/
│       ├── orchestrator/
│       └── workflows/
├── shared/
│   ├── models/
│   ├── utils/
│   └── constants/
├── config/
│   ├── development.json
│   ├── production.json
│   └── test.json
└── docs/
    ├── api/
    ├── guides/
    └── examples/
```

### 2. Coding Standards

```javascript
// Tool Implementation Pattern
class MCPTool {
    constructor(name, schema) {
        this.name = name;
        this.schema = schema;
        this.validator = new Validator(schema);
    }
    
    async execute(params) {
        // 1. Validate input
        const validation = this.validator.validate(params);
        if (!validation.valid) {
            throw new ValidationError(validation.errors);
        }
        
        // 2. Execute business logic
        try {
            const result = await this.performOperation(params);
            
            // 3. Transform output
            return this.transformOutput(result);
            
        } catch (error) {
            // 4. Error handling
            return this.handleError(error);
        }
    }
}
```

### 3. Testing Strategy

```javascript
// Unit Test Pattern
describe('OCR Tool', () => {
    let ocrTool;
    
    beforeEach(() => {
        ocrTool = new OCRTool();
    });
    
    it('should extract text from image', async () => {
        const result = await ocrTool.execute({
            file_path: '/test/image.jpg'
        });
        
        expect(result.success).toBe(true);
        expect(result.text).toBeDefined();
    });
    
    it('should handle invalid file gracefully', async () => {
        const result = await ocrTool.execute({
            file_path: '/invalid/path.jpg'
        });
        
        expect(result.success).toBe(false);
        expect(result.error).toBeDefined();
    });
});
```

### 4. Performance Optimization

```javascript
// Caching Strategy
class CacheManager {
    constructor(options = {}) {
        this.cache = new LRUCache({
            max: options.maxSize || 1000,
            ttl: options.ttl || 3600000, // 1 hour
            updateAgeOnGet: true
        });
    }
    
    async get(key, factory) {
        let value = this.cache.get(key);
        
        if (value === undefined) {
            value = await factory();
            this.cache.set(key, value);
        }
        
        return value;
    }
}

// Connection Pooling
class OdooConnectionPool {
    constructor(config) {
        this.pool = [];
        this.config = config;
        this.maxConnections = config.maxConnections || 10;
    }
    
    async getConnection() {
        if (this.pool.length > 0) {
            return this.pool.pop();
        }
        
        if (this.activeConnections < this.maxConnections) {
            return this.createConnection();
        }
        
        // Wait for available connection
        return this.waitForConnection();
    }
}
```

---

## API Reference

### MCP Protocol Messages

```typescript
// Request Format
interface MCPRequest {
    jsonrpc: "2.0"
    id: string | number
    method: "tools/call" | "tools/list"
    params: {
        name?: string
        arguments?: any
    }
}

// Response Format
interface MCPResponse {
    jsonrpc: "2.0"
    id: string | number
    result?: {
        content: Array<{
            type: "text"
            text: string
        }>
    }
    error?: {
        code: number
        message: string
        data?: any
    }
}
```

### Tool Schemas

```javascript
// Example Tool Schema
const processImageSchema = {
    type: 'object',
    properties: {
        file_path: {
            type: 'string',
            description: 'Absolute path to image file'
        },
        extract_structured_data: {
            type: 'boolean',
            description: 'Extract structured data from image',
            default: false
        }
    },
    required: ['file_path']
};
```

---

## Deployment Architecture

### 1. Development Environment

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  mcp-ecosystem:
    build: .
    volumes:
      - ./servers:/app/servers
      - ./config:/app/config
    environment:
      - NODE_ENV=development
      - ODOO_URL=${ODOO_URL}
      - ODOO_API_KEY=${ODOO_API_KEY}
    ports:
      - "3000:3000"
    
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### 2. Production Deployment

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-ecosystem
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-ecosystem
  template:
    metadata:
      labels:
        app: mcp-ecosystem
    spec:
      containers:
      - name: mcp-servers
        image: mcp-ecosystem:latest
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        env:
        - name: NODE_ENV
          value: "production"
        - name: ODOO_API_KEY
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: odoo-api-key
```

### 3. Monitoring & Observability

```javascript
// Prometheus Metrics
class MetricsCollector {
    constructor() {
        this.register = new prometheus.Registry();
        
        this.toolCallCounter = new prometheus.Counter({
            name: 'mcp_tool_calls_total',
            help: 'Total number of tool calls',
            labelNames: ['server', 'tool', 'status']
        });
        
        this.toolDuration = new prometheus.Histogram({
            name: 'mcp_tool_duration_seconds',
            help: 'Tool execution duration',
            labelNames: ['server', 'tool'],
            buckets: [0.1, 0.5, 1, 2, 5, 10]
        });
        
        this.register.registerMetric(this.toolCallCounter);
        this.register.registerMetric(this.toolDuration);
    }
}
```

---

## Error Handling & Recovery

### 1. Error Types

```javascript
class MCPError extends Error {
    constructor(message, code, details) {
        super(message);
        this.code = code;
        this.details = details;
    }
}

class ValidationError extends MCPError {
    constructor(errors) {
        super('Validation failed', 'VALIDATION_ERROR', errors);
    }
}

class NetworkError extends MCPError {
    constructor(message, originalError) {
        super(message, 'NETWORK_ERROR', { originalError });
    }
}

class AuthenticationError extends MCPError {
    constructor(message) {
        super(message, 'AUTH_ERROR', {});
    }
}
```

### 2. Retry Logic

```javascript
class RetryManager {
    async executeWithRetry(fn, options = {}) {
        const maxRetries = options.maxRetries || 3;
        const backoffMultiplier = options.backoffMultiplier || 2;
        let lastError;
        
        for (let attempt = 0; attempt < maxRetries; attempt++) {
            try {
                return await fn();
            } catch (error) {
                lastError = error;
                
                if (!this.isRetryable(error) || attempt === maxRetries - 1) {
                    throw error;
                }
                
                const delay = Math.pow(backoffMultiplier, attempt) * 1000;
                await this.sleep(delay);
            }
        }
        
        throw lastError;
    }
    
    isRetryable(error) {
        return error instanceof NetworkError || 
               error.code === 'ECONNRESET' ||
               error.code === 'ETIMEDOUT';
    }
}
```

---

## Performance Benchmarks

### OCR Processing Performance

| Operation | CPU Time | GPU Time | Speedup |
|-----------|----------|----------|---------|
| Single Image (HEIF) | 25-40s | 15-25s | 1.5-2x |
| PDF (5 pages) | 60-80s | 30-40s | 2x |
| Batch (10 images) | 250-300s | 120-150s | 2-2.5x |

### Memory Usage

```javascript
// Memory monitoring
class MemoryMonitor {
    static getUsage() {
        const usage = process.memoryUsage();
        return {
            rss: (usage.rss / 1024 / 1024).toFixed(2) + ' MB',
            heapTotal: (usage.heapTotal / 1024 / 1024).toFixed(2) + ' MB',
            heapUsed: (usage.heapUsed / 1024 / 1024).toFixed(2) + ' MB',
            external: (usage.external / 1024 / 1024).toFixed(2) + ' MB'
        };
    }
}
```

---

## Future Architecture Considerations

### 1. Scaling Strategy

- **Horizontal Scaling**: Deploy multiple MCP server instances
- **Load Balancing**: Implement request distribution
- **Queue System**: Add RabbitMQ/Kafka for async processing
- **Caching Layer**: Redis for distributed caching

### 2. Microservices Migration

```yaml
# Future microservices architecture
services:
  - name: ocr-service
    replicas: 5
    gpu: enabled
    
  - name: odoo-sync-service
    replicas: 3
    
  - name: excel-generator-service
    replicas: 2
    
  - name: workflow-orchestrator
    replicas: 2
```

### 3. API Gateway

```javascript
// Future API Gateway implementation
class APIGateway {
    constructor() {
        this.router = new Router();
        this.rateLimiter = new RateLimiter();
        this.auth = new AuthMiddleware();
    }
    
    setupRoutes() {
        this.router.post('/api/v1/process-document',
            this.auth.verify,
            this.rateLimiter.limit,
            this.processDocument
        );
    }
}
```

---

This technical architecture provides the foundation for building a robust, scalable document processing and Odoo integration platform using the MCP ecosystem.
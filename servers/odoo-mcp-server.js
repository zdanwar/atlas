#!/usr/bin/env node

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { 
    CallToolRequestSchema,
    ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');
const https = require('https');

// SSL BYPASS FOR ODOO CONNECTION
process.env["NODE_TLS_REJECT_UNAUTHORIZED"] = 0;

// Odoo connection configuration
const ODOO_CONFIG = {
    hostname: 'zdanwar-milestonealuminium.odoo.com',
    database: 'zdanwar-milestonealuminium-main-17798127',
    username: 'zaiddanishanwar@gmail.com',
    apiKey: '0700623eddc908552e04249a58de0707eed437d0'
};

// Global variable to store authenticated user ID
let userId = null;

// Function to make Odoo API requests
function makeOdooRequest(data) {
    return new Promise((resolve, reject) => {
        const postData = JSON.stringify(data);
        
        const options = {
            hostname: ODOO_CONFIG.hostname,
            port: 443,
            path: '/jsonrpc',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData)
            },
            rejectUnauthorized: false
        };

        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(body));
                } catch (e) {
                    reject(e);
                }
            });
        });

        req.on('error', reject);
        req.write(postData);
        req.end();
    });
}

// Authentication function
async function authenticate() {
    if (userId) return userId;
    
    const response = await makeOdooRequest({
        jsonrpc: '2.0',
        method: 'call',
        params: {
            service: 'common',
            method: 'authenticate',
            args: [ODOO_CONFIG.database, ODOO_CONFIG.username, ODOO_CONFIG.apiKey, {}]
        },
        id: 1
    });
    
    if (response.result) {
        userId = response.result;
        return userId;
    } else {
        throw new Error('Authentication failed');
    }
}

// Create the MCP server
const server = new Server(
    {
        name: 'odoo-server',
        version: '0.2.0',
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
                name: 'search_partners',
                description: 'Search for partners/contacts in Odoo',
                inputSchema: {
                    type: 'object',
                    properties: {
                        domain: { type: 'array', description: 'Search domain (optional)', default: [] },
                        limit: { type: 'number', description: 'Number of records to return', default: 10 }
                    }
                }
            },
            {
                name: 'search_products',
                description: 'Search for products in Odoo',
                inputSchema: {
                    type: 'object',
                    properties: {
                        domain: { type: 'array', description: 'Search domain (optional)', default: [] },
                        limit: { type: 'number', description: 'Number of records to return', default: 10 }
                    }
                }
            },
            {
                name: 'search_sales_orders',
                description: 'Search for sales orders in Odoo',
                inputSchema: {
                    type: 'object',
                    properties: {
                        domain: { type: 'array', description: 'Search domain (optional)', default: [] },
                        limit: { type: 'number', description: 'Number of records to return', default: 10 }
                    }
                }
            },
            {
                name: 'search_invoices',
                description: 'Search for invoices in Odoo',
                inputSchema: {
                    type: 'object',
                    properties: {
                        domain: { type: 'array', description: 'Search domain (optional)', default: [] },
                        limit: { type: 'number', description: 'Number of records to return', default: 10 }
                    }
                }
            },
            {
                name: 'search_stock_moves',
                description: 'Search for stock movements in Odoo',
                inputSchema: {
                    type: 'object',
                    properties: {
                        domain: { type: 'array', description: 'Search domain (optional)', default: [] },
                        limit: { type: 'number', description: 'Number of records to return', default: 10 }
                    }
                }
            },
            {
                name: 'search_users',
                description: 'Search for users in Odoo',
                inputSchema: {
                    type: 'object',
                    properties: {
                        domain: { type: 'array', description: 'Search domain (optional)', default: [] },
                        limit: { type: 'number', description: 'Number of records to return', default: 10 }
                    }
                }
            },
            {
                name: 'search_companies',
                description: 'Search for companies in Odoo',
                inputSchema: {
                    type: 'object',
                    properties: {
                        domain: { type: 'array', description: 'Search domain (optional)', default: [] },
                        limit: { type: 'number', description: 'Number of records to return', default: 10 }
                    }
                }
            },
            {
                name: 'get_database_info',
                description: 'Get general information about the Odoo database',
                inputSchema: { type: 'object', properties: {} }
            },
            {
                name: 'get_chart_of_accounts',
                description: 'Get chart of accounts structure',
                inputSchema: { type: 'object', properties: {} }
            },
            {
                name: 'get_financial_summary',
                description: 'Get financial summary and key metrics',
                inputSchema: { type: 'object', properties: {} }
            },
            {
                name: 'get_module_status',
                description: 'Get installed modules and their status',
                inputSchema: { type: 'object', properties: {} }
            }
        ],
    };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
        await authenticate();

        switch (name) {
            case 'search_partners':
                const partnersResponse = await makeOdooRequest({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        service: 'object',
                        method: 'execute_kw',
                        args: [ODOO_CONFIG.database, userId, ODOO_CONFIG.apiKey, 'res.partner', 'search_read',
                               [args.domain || []], 
                               { fields: ['name', 'email', 'phone', 'is_company', 'city', 'country_id'], limit: args.limit || 10 }]
                    },
                    id: 2
                });

                return {
                    content: [{
                        type: 'text',
                        text: `Found ${partnersResponse.result.length} partners:\n\n` +
                              partnersResponse.result.map(partner => 
                                  `• ${partner.name} (${partner.is_company ? 'Company' : 'Person'})\n` +
                                  `  Email: ${partner.email || 'N/A'}\n` +
                                  `  Phone: ${partner.phone || 'N/A'}\n` +
                                  `  Location: ${partner.city || 'N/A'}, ${partner.country_id ? partner.country_id[1] : 'N/A'}\n`
                              ).join('\n')
                    }]
                };

            case 'search_products':
                const productsResponse = await makeOdooRequest({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        service: 'object',
                        method: 'execute_kw',
                        args: [ODOO_CONFIG.database, userId, ODOO_CONFIG.apiKey, 'product.product', 'search_read',
                               [args.domain || []], 
                               { fields: ['name', 'list_price', 'standard_price', 'qty_available', 'categ_id'], limit: args.limit || 10 }]
                    },
                    id: 3
                });

                return {
                    content: [{
                        type: 'text',
                        text: `Found ${productsResponse.result.length} products:\n\n` +
                              productsResponse.result.map(product => 
                                  `• ${product.name}\n` +
                                  `  Category: ${product.categ_id ? product.categ_id[1] : 'N/A'}\n` +
                                  `  Sale Price: $${product.list_price || 0}\n` +
                                  `  Cost: $${product.standard_price || 0}\n` +
                                  `  Stock: ${product.qty_available || 0}\n`
                              ).join('\n')
                    }]
                };

            case 'search_sales_orders':
                const salesResponse = await makeOdooRequest({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        service: 'object',
                        method: 'execute_kw',
                        args: [ODOO_CONFIG.database, userId, ODOO_CONFIG.apiKey, 'sale.order', 'search_read',
                               [args.domain || []], 
                               { fields: ['name', 'partner_id', 'date_order', 'state', 'amount_total'], limit: args.limit || 10 }]
                    },
                    id: 4
                });

                return {
                    content: [{
                        type: 'text',
                        text: `Found ${salesResponse.result.length} sales orders:\n\n` +
                              salesResponse.result.map(order => 
                                  `• ${order.name} - ${order.partner_id ? order.partner_id[1] : 'No Customer'}\n` +
                                  `  Date: ${order.date_order}\n` +
                                  `  Status: ${order.state}\n` +
                                  `  Total: $${order.amount_total || 0}\n`
                              ).join('\n')
                    }]
                };

            case 'search_invoices':
                const invoicesResponse = await makeOdooRequest({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        service: 'object',
                        method: 'execute_kw',
                        args: [ODOO_CONFIG.database, userId, ODOO_CONFIG.apiKey, 'account.move', 'search_read',
                               [args.domain || [['move_type', 'in', ['out_invoice', 'in_invoice']]]], 
                               { fields: ['name', 'partner_id', 'invoice_date', 'state', 'amount_total', 'move_type'], limit: args.limit || 10 }]
                    },
                    id: 5
                });

                return {
                    content: [{
                        type: 'text',
                        text: `Found ${invoicesResponse.result.length} invoices:\n\n` +
                              invoicesResponse.result.map(invoice => 
                                  `• ${invoice.name} - ${invoice.partner_id ? invoice.partner_id[1] : 'No Partner'}\n` +
                                  `  Type: ${invoice.move_type === 'out_invoice' ? 'Customer Invoice' : 'Vendor Bill'}\n` +
                                  `  Date: ${invoice.invoice_date}\n` +
                                  `  Status: ${invoice.state}\n` +
                                  `  Total: $${invoice.amount_total || 0}\n`
                              ).join('\n')
                    }]
                };

            case 'search_stock_moves':
                const stockResponse = await makeOdooRequest({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        service: 'object',
                        method: 'execute_kw',
                        args: [ODOO_CONFIG.database, userId, ODOO_CONFIG.apiKey, 'stock.move', 'search_read',
                               [args.domain || []], 
                               { fields: ['name', 'product_id', 'product_uom_qty', 'state', 'date', 'location_id', 'location_dest_id'], limit: args.limit || 10 }]
                    },
                    id: 6
                });

                return {
                    content: [{
                        type: 'text',
                        text: `Found ${stockResponse.result.length} stock movements:\n\n` +
                              stockResponse.result.map(move => 
                                  `• ${move.name}\n` +
                                  `  Product: ${move.product_id ? move.product_id[1] : 'N/A'}\n` +
                                  `  Quantity: ${move.product_uom_qty || 0}\n` +
                                  `  Status: ${move.state}\n` +
                                  `  Date: ${move.date}\n`
                              ).join('\n')
                    }]
                };

            case 'search_users':
                const usersResponse = await makeOdooRequest({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        service: 'object',
                        method: 'execute_kw',
                        args: [ODOO_CONFIG.database, userId, ODOO_CONFIG.apiKey, 'res.users', 'search_read',
                               [args.domain || []], 
                               { fields: ['name', 'login', 'active', 'groups_id'], limit: args.limit || 10 }]
                    },
                    id: 7
                });

                return {
                    content: [{
                        type: 'text',
                        text: `Found ${usersResponse.result.length} users:\n\n` +
                              usersResponse.result.map(user => 
                                  `• ${user.name}\n` +
                                  `  Login: ${user.login}\n` +
                                  `  Active: ${user.active ? 'Yes' : 'No'}\n` +
                                  `  Groups: ${user.groups_id ? user.groups_id.length : 0} permission groups\n`
                              ).join('\n')
                    }]
                };

            case 'search_companies':
                const companiesResponse = await makeOdooRequest({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        service: 'object',
                        method: 'execute_kw',
                        args: [ODOO_CONFIG.database, userId, ODOO_CONFIG.apiKey, 'res.company', 'search_read',
                               [args.domain || []], 
                               { fields: ['name', 'email', 'phone', 'website', 'currency_id', 'country_id'], limit: args.limit || 10 }]
                    },
                    id: 8
                });

                return {
                    content: [{
                        type: 'text',
                        text: `Found ${companiesResponse.result.length} companies:\n\n` +
                              companiesResponse.result.map(company => 
                                  `• ${company.name}\n` +
                                  `  Email: ${company.email || 'N/A'}\n` +
                                  `  Phone: ${company.phone || 'N/A'}\n` +
                                  `  Currency: ${company.currency_id ? company.currency_id[1] : 'N/A'}\n` +
                                  `  Country: ${company.country_id ? company.country_id[1] : 'N/A'}\n`
                              ).join('\n')
                    }]
                };

            case 'get_database_info':
                const partnerCount = await makeOdooRequest({
                    jsonrpc: '2.0', method: 'call',
                    params: { service: 'object', method: 'execute_kw',
                        args: [ODOO_CONFIG.database, userId, ODOO_CONFIG.apiKey, 'res.partner', 'search_count', [[]]] },
                    id: 9
                });

                const productCount = await makeOdooRequest({
                    jsonrpc: '2.0', method: 'call',
                    params: { service: 'object', method: 'execute_kw',
                        args: [ODOO_CONFIG.database, userId, ODOO_CONFIG.apiKey, 'product.product', 'search_count', [[]]] },
                    id: 10
                });

                const salesCount = await makeOdooRequest({
                    jsonrpc: '2.0', method: 'call',
                    params: { service: 'object', method: 'execute_kw',
                        args: [ODOO_CONFIG.database, userId, ODOO_CONFIG.apiKey, 'sale.order', 'search_count', [[]]] },
                    id: 11
                });

                return {
                    content: [{
                        type: 'text',
                        text: `Odoo Database Information:\n\n` +
                              `• Database: ${ODOO_CONFIG.database}\n` +
                              `• Total Partners/Contacts: ${partnerCount.result}\n` +
                              `• Total Products: ${productCount.result}\n` +
                              `• Total Sales Orders: ${salesCount.result}\n` +
                              `• Connected User ID: ${userId}\n`
                    }]
                };

            case 'get_chart_of_accounts':
                const accountsResponse = await makeOdooRequest({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        service: 'object',
                        method: 'execute_kw',
                        args: [ODOO_CONFIG.database, userId, ODOO_CONFIG.apiKey, 'account.account', 'search_read',
                               [[]], 
                               { fields: ['code', 'name', 'account_type', 'reconcile'], limit: 50 }]
                    },
                    id: 12
                });

                return {
                    content: [{
                        type: 'text',
                        text: `Chart of Accounts (${accountsResponse.result.length} accounts):\n\n` +
                              accountsResponse.result.map(account => 
                                  `• ${account.code} - ${account.name}\n` +
                                  `  Type: ${account.account_type}\n` +
                                  `  Reconcile: ${account.reconcile ? 'Yes' : 'No'}\n`
                              ).join('\n')
                    }]
                };

            case 'get_financial_summary':
                const invoiceTotal = await makeOdooRequest({
                    jsonrpc: '2.0', method: 'call',
                    params: { service: 'object', method: 'execute_kw',
                        args: [ODOO_CONFIG.database, userId, ODOO_CONFIG.apiKey, 'account.move', 'search_count', 
                               [['move_type', 'in', ['out_invoice', 'in_invoice']]]] },
                    id: 13
                });

                return {
                    content: [{
                        type: 'text',
                        text: `Financial Summary:\n\n` +
                              `• Total Invoices: ${invoiceTotal.result}\n` +
                              `• Partners: ${await (await makeOdooRequest({jsonrpc: '2.0', method: 'call', params: {service: 'object', method: 'execute_kw', args: [ODOO_CONFIG.database, userId, ODOO_CONFIG.apiKey, 'res.partner', 'search_count', [[]]]}, id: 14})).result}\n` +
                              `• Products: ${await (await makeOdooRequest({jsonrpc: '2.0', method: 'call', params: {service: 'object', method: 'execute_kw', args: [ODOO_CONFIG.database, userId, ODOO_CONFIG.apiKey, 'product.product', 'search_count', [[]]]}, id: 15})).result}\n`
                    }]
                };

            case 'get_module_status':
                const modulesResponse = await makeOdooRequest({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        service: 'object',
                        method: 'execute_kw',
                        args: [ODOO_CONFIG.database, userId, ODOO_CONFIG.apiKey, 'ir.module.module', 'search_read',
                               [['state', '=', 'installed']], 
                               { fields: ['name', 'shortdesc', 'version'], limit: 20 }]
                    },
                    id: 16
                });

                return {
                    content: [{
                        type: 'text',
                        text: `Installed Modules (${modulesResponse.result.length} shown):\n\n` +
                              modulesResponse.result.map(module => 
                                  `• ${module.name} - ${module.shortdesc}\n` +
                                  `  Version: ${module.version}\n`
                              ).join('\n')
                    }]
                };

            default:
                throw new Error(`Unknown tool: ${name}`);
        }
    } catch (error) {
        return {
            content: [{
                type: 'text',
                text: `Error: ${error.message}`
            }],
            isError: true,
        };
    }
});

// Start the server
async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error('Enhanced Odoo MCP server running on stdio');
}

main().catch(console.error);

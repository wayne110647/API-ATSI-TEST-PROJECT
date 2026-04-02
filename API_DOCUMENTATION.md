# Master Data API Documentation

This module provides a REST-like API (JSON-RPC) for creating master data in Odoo 17.

## Base URL
The API is available at: `http://<odoo_server_url>`

## Authentication
Routes are configured with `auth='public'` implementation uses `sudo()`. 
**Note:** In a production environment, you should secure these endpoints or use `auth='user'`/`auth='api_key'`.

## Endpoints

All endpoints accept `POST` requests with a JSON body following Odoo's JSON-RPC format:
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    ... data fields ...
  },
  "id": 1
}
```

### 1. Create Customer
**Endpoint:** `/master_api/create/customer`

**Payload:**
```json
{
  "params": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "1234567890",
    "street": "123 Main St",
    "city": "Bangkok"
  }
}
```

### 2. Create Vendor
**Endpoint:** `/master_api/create/vendor`

**Payload:**
```json
{
  "params": {
    "name": "Supplier Co.",
    "email": "supply@example.com",
    "vat": "123456789"
  }
}
```

### 3. Create Product
**Endpoint:** `/master_api/create/product`

**Payload:**
```json
{
  "params": {
    "name": "New Product",
    "list_price": 100.0,
    "standard_price": 80.0,
    "type": "consu"  // consu, service, product
  }
}
```

### 4. Create Employee
**Endpoint:** `/master_api/create/employee`

**Payload:**
```json
{
  "params": {
    "name": "Jane Smith",
    "work_email": "jane@company.com",
    "department_id": 1, // Optional: Integer ID of existing department
    "job_id": 1 // Optional: Integer ID of existing job position
  }
}
```

### 5. Create Chart of Account
**Endpoint:** `/master_api/create/coa`

**Payload:**
```json
{
  "params": {
    "name": "Petty Cash",
    "code": "110100",
    "account_type": "asset_cash",
    "reconcile": true
  }
}
```
**Common Account Types:**
- `asset_receivable`
- `asset_cash`
- `asset_current`
- `asset_fixed`
- `liability_payable`
- `liability_current`
- `equity`
- `income`
- `expense`

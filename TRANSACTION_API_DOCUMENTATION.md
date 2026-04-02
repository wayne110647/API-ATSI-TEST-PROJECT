# Transaction API Documentation

This module provides a REST-like API (JSON-RPC) for creating transaction data in Odoo 17.
These endpoints are handled by the `TransactionsController`.

## Base URL
`http://<odoo_server_url>`

## Endpoints

### 1. Create Sale Order
**Endpoint:** `/master_api/create/sale_order`
**Method:** `POST`

**Payload (Header only):**
```json
{
  "params": {
    "partner_id": 10,
    "date_order": "2023-10-27"
  }
}
```

**Payload (With Lines):**
```json
{
  "params": {
    "partner_id": 10,
    "order_line": [
        [0, 0, {"product_id": 5, "product_uom_qty": 2}],
        [0, 0, {"product_id": 6, "product_uom_qty": 5}]
    ]
  }
}
```

### 2. Create Sale Order Line (Add to existing Order)
**Endpoint:** `/master_api/create/sale_order_line`

**Payload:**
```json
{
  "params": {
    "order_id": 25,
    "product_id": 5,
    "product_uom_qty": 3,
    "price_unit": 500.0
  }
}
```

### 3. Create Purchase Order
**Endpoint:** `/master_api/create/purchase_order`

**Payload:**
```json
{
  "params": {
    "partner_id": 12,
    "order_line": [
        [0, 0, {"product_id": 5, "product_qty": 10}]
    ]
  }
}
```

### 4. Create Purchase Order Line
**Endpoint:** `/master_api/create/purchase_order_line`

**Payload:**
```json
{
  "params": {
    "order_id": 26,
    "product_id": 5,
    "product_qty": 10,
    "price_unit": 200.0
  }
}
```

### 5. Create Goods Receive (Incoming Shipment)
**Endpoint:** `/master_api/create/goods_receive`

**Payload:**
```json
{
  "params": {
    "partner_id": 12,
    "picking_type_id": 1, // Optional, can be auto-detected if simple setup
    "move_ids_without_package": [
        [0, 0, {
            "name": "Product A",
            "product_id": 5,
            "product_uom_qty": 10,
            "location_id": 4, // Vendor Location
            "location_dest_id": 8 // Stock
        }]
    ]
  }
}
```

### 6. Create Goods Issue (Delivery Order)
**Endpoint:** `/master_api/create/goods_issue`

**Payload:**
```json
{
  "params": {
    "partner_id": 10,
    "picking_type_id": 2, // Optional
    "move_ids_without_package": [
        [0, 0, {
            "name": "Product A",
            "product_id": 5,
            "product_uom_qty": 2,
            "location_id": 8, // Stock
            "location_dest_id": 5 // Customer Location
        }]
    ]
  }
}
```

### 7. Create Goods Transfer (Internal Transfer)
**Endpoint:** `/master_api/create/goods_transfer`

**Payload:**
```json
{
  "params": {
    "picking_type_id": 3, // Internal Type
    "location_id": 8, // Stock
    "location_dest_id": 9, // Shelf 1
    "move_ids_without_package": [
        [0, 0, {
            "name": "Product A",
            "product_id": 5,
            "product_uom_qty": 5,
            "location_id": 8,
            "location_dest_id": 9
        }]
    ]
  }
}
```

 
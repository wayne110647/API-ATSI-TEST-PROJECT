from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class TransactionsController(http.Controller):

    def _response(self, result=None, error=None):
        if error:
            return {'status': 'error', 'message': str(error)}
        return {'status': 'success', 'data': result}

    # --- Sale Order ---
    @http.route('/master_api/create/sale_order', type='json', auth='public', methods=['POST'], csrf=False)
    def create_sale_order(self, **kwargs):
        """
        http://localhost:8069/master_api/create/sale_order
        Create Sale Order API.
       {
    "jsonrpc": "2.0",
    "params": {
        "partner_id": "ลูกค้าใหม่ จำกัด",  // ถ้าไม่เจอ สร้างใหม่
        "date_order": "2024-02-10",
        "order_line": [
            {
                "product_id": "สินค้าใหม่ A", // ถ้าไม่เจอ สร้างใหม่
                "product_uom_qty": 5,
                "price_unit": 100
            },
            {
                "product_id": "สินค้าใหม่ B", // ถ้าไม่เจอ สร้างใหม่
                "product_uom_qty": 2,
                  "price_unit": 300
            }
        ]
    }
}
        """
        try:
            record = request.env['transaction.api'].sudo().create_sale_order(kwargs)
            return self._response(result={'id': record.id, 'name': record.name})
        except Exception as e:
            _logger.error("Error creating sale order: %s", e)
            return self._response(error=e)

    @http.route('/master_api/create/sale_order_line', type='json', auth='public', methods=['POST'], csrf=False)
    def create_sale_order_line(self, **kwargs):
        try:
            record = request.env['transaction.api'].sudo().create_sale_order_line(kwargs)
            return self._response(result={'id': record.id, 'order_id': record.order_id.id})
        except Exception as e:
            _logger.error("Error creating sale order line: %s", e)
            return self._response(error=e)

    # --- Purchase Order ---
    @http.route('/master_api/create/purchase_order', type='json', auth='public', methods=['POST'], csrf=False)
    def create_purchase_order(self, **kwargs):
        """
        Create Purchase Order API.
       {
    "jsonrpc": "2.0",
    "params": {
        "partner_id": "ผู้ขายรายใหม่ จำกัด", // ถ้าไม่เจอ สร้างใหม่
        "order_line": [
            {
                "product_id": "วัตถุดิบใหม่ X", // ถ้าไม่เจอ สร้างใหม่
                "product_qty": 50,
                "price_unit": 20
            }
        ]
    }
}
        """
        try:
            record = request.env['transaction.api'].sudo().create_purchase_order(kwargs)
            return self._response(result={'id': record.id, 'name': record.name})
        except Exception as e:
            _logger.error("Error creating purchase order: %s", e)
            return self._response(error=e)

    @http.route('/master_api/create/purchase_order_line', type='json', auth='public', methods=['POST'], csrf=False)
    def create_purchase_order_line(self, **kwargs):
        try:
            record = request.env['transaction.api'].sudo().create_purchase_order_line(kwargs)
            return self._response(result={'id': record.id, 'order_id': record.order_id.id})
        except Exception as e:
            _logger.error("Error creating purchase order line: %s", e)
            return self._response(error=e)

    # --- Stock Picking (Goods Receive/Issue/Transfer) ---
    @http.route('/master_api/create/goods_receive', type='json', auth='public', methods=['POST'], csrf=False)
    def create_goods_receive(self, **kwargs):
        """
        Create Goods Receive API (Incoming Shipment).
        Payload: {
            "params": {
                "partner_id": 1,
                "picking_type_id": 1,  # Optional if only one incoming type exists
                "location_id": 4,      # Optional (Vendor Location)
                "location_dest_id": 8, # Optional (Stock)
                "move_lines": [
                    {"product_id": 10, "product_uom_qty": 10, "name": "Item 10"},
                    {"product_id": 11, "product_uom_qty": 5}
                ]
            }
        }
        """
        try:
            # incoming
            record = request.env['transaction.api'].sudo().create_picking(kwargs, picking_type_code='incoming')
            return self._response(result={'id': record.id, 'name': record.name})
        except Exception as e:
            _logger.error("Error creating goods receive: %s", e)
            return self._response(error=e)

    @http.route('/master_api/create/goods_issue', type='json', auth='public', methods=['POST'], csrf=False)
    def create_goods_issue(self, **kwargs):
        """
        Create Goods Issue API (Delivery Order).
        Payload: {
            "params": {
                "partner_id": 1,
                "location_id": 8,      # Optional (Stock)
                "location_dest_id": 5, # Optional (Customer Location)
                "move_lines": [
                    {"product_id": 10, "product_uom_qty": 2}
                ]
            }
        }
        """
        try:
            # outgoing
            record = request.env['transaction.api'].sudo().create_picking(kwargs, picking_type_code='outgoing')
            return self._response(result={'id': record.id, 'name': record.name})
        except Exception as e:
            _logger.error("Error creating goods issue: %s", e)
            return self._response(error=e)

    @http.route('/master_api/create/goods_transfer', type='json', auth='public', methods=['POST'], csrf=False)
    def create_goods_transfer(self, **kwargs):
        """
        Create Internal Transfer API.
        Payload: {
            "params": {
                "location_id": 8,       # Required (Source Location)
                "location_dest_id": 9,  # Required (Dest Location)
                "move_lines": [
                    {"product_id": 10, "product_uom_qty": 5}
                ]
            }
        }
        """
        try:
            # internal
            record = request.env['transaction.api'].sudo().create_picking(kwargs, picking_type_code='internal')
            return self._response(result={'id': record.id, 'name': record.name})
        except Exception as e:
            _logger.error("Error creating goods transfer: %s", e)
            return self._response(error=e)



from odoo import models, api, _

class TransactionApi(models.AbstractModel):
    _name = 'transaction.api'
    _description = 'Transaction Data Creation API Helper'

    @api.model
    def _get_partner_id(self, vals):
        """Helper to find partner_id from partner_name if partner_id is not integer. Creates if not found."""
        if 'partner_id' in vals:
            if isinstance(vals['partner_id'], str):
                # Search by name
                partner = self.env['res.partner'].search([('name', '=', vals['partner_id'])], limit=1)
                if partner:
                    vals['partner_id'] = partner.id
                else:
                    # Create new partner if not found
                    partner = self.env['res.partner'].create({'name': vals['partner_id']})
                    vals['partner_id'] = partner.id
            elif 'partner_name' in vals and not vals.get('partner_id'):
                partner = self.env['res.partner'].search([('name', '=', vals['partner_name'])], limit=1)
                if partner:
                    vals['partner_id'] = partner.id
                else:
                    # Create new partner if not found
                    partner = self.env['res.partner'].create({'name': vals['partner_name']})
                    vals['partner_id'] = partner.id
        elif 'partner_name' in vals:
             partner = self.env['res.partner'].search([('name', '=', vals['partner_name'])], limit=1)
             if partner:
                 vals['partner_id'] = partner.id
             else:
                # Create new partner if not found
                partner = self.env['res.partner'].create({'name': vals['partner_name']})
                vals['partner_id'] = partner.id
        return vals

    @api.model
    def _get_product_id(self, vals):
        """Helper to find product_id from product_name if product_id is not integer. Creates if not found."""
        if 'product_id' in vals:
            if isinstance(vals['product_id'], str):
                product = self.env['product.product'].search([('name', '=', vals['product_id'])], limit=1)
                if product:
                    vals['product_id'] = product.id
                else:
                    # Create new product if not found
                    product = self.env['product.product'].create({'name': vals['product_id']})
                    vals['product_id'] = product.id
        elif 'product_name' in vals and not vals.get('product_id'):
            product = self.env['product.product'].search([('name', '=', vals['product_name'])], limit=1)
            if product:
                vals['product_id'] = product.id
            else:
                # Create new product if not found
                product = self.env['product.product'].create({'name': vals['product_name']})
                vals['product_id'] = product.id
        return vals

    @api.model
    def create_sale_order(self, vals):
        """
        Create Sale Order (sale.order).
        Required: partner_id
        Optional: order_line (list of dicts)
        """
        vals = self._get_partner_id(vals)

        # Support creating lines inline if provided as list of dicts
        order_lines = vals.get('order_line')
        if order_lines and isinstance(order_lines, list):
            # Check if it has items and the first item is a dict (to avoid re-wrapping tuples)
            if len(order_lines) > 0 and isinstance(order_lines[0], dict):
                # Resolve product_id for each line
                for line in order_lines:
                    self._get_product_id(line)
                vals['order_line'] = [(0, 0, line) for line in order_lines]
                
        return self.env['sale.order'].create(vals)

    @api.model
    def create_sale_order_line(self, vals):
        """
        Create Sale Order Line (sale.order.line).
        Required: order_id, product_id
        """
        vals = self._get_product_id(vals)
        return self.env['sale.order.line'].create(vals)

    @api.model
    def create_purchase_order(self, vals):
        """
        Create Purchase Order (purchase.order).
        Required: partner_id
        Optional: order_line
        """
        vals = self._get_partner_id(vals)

        # Support creating lines inline if provided as list of dicts
        order_lines = vals.get('order_line')
        if order_lines and isinstance(order_lines, list):
            # Check if it has items and the first item is a dict (to avoid re-wrapping tuples)
            if len(order_lines) > 0 and isinstance(order_lines[0], dict):
                 # Resolve product_id for each line
                for line in order_lines:
                    self._get_product_id(line)
                vals['order_line'] = [(0, 0, line) for line in order_lines]
                
        return self.env['purchase.order'].create(vals)

    @api.model
    def create_purchase_order_line(self, vals):
        """
        Create Purchase Order Line (purchase.order.line).
        Required: order_id, product_id
        """
        vals = self._get_product_id(vals)
        return self.env['purchase.order.line'].create(vals)

    @api.model
    def create_picking(self, vals, picking_type_code):
        """
        Create Stock Picking (stock.picking).
        picking_type_code: 'incoming', 'outgoing', 'internal'
        Required: location_id, location_dest_id, picking_type_id (or inferred)
        """
        vals = self._get_partner_id(vals)

        if 'picking_type_id' not in vals:
            # Try to find a picking type
            domain = [('code', '=', picking_type_code)]
            # You might want to filter by warehouse if provided, defaulting to first one found
            picking_type = self.env['stock.picking.type'].search(domain, limit=1)
            if picking_type:
                vals['picking_type_id'] = picking_type.id
                if 'location_id' not in vals:
                    vals['location_id'] = picking_type.default_location_src_id.id if picking_type.default_location_src_id else False
                if 'location_dest_id' not in vals:
                    vals['location_dest_id'] = picking_type.default_location_dest_id.id if picking_type.default_location_dest_id else False
        
        # Support inline moves
        move_lines = vals.get('move_lines') or vals.get('move_ids')
        if move_lines and isinstance(move_lines, list):
            if len(move_lines) > 0 and isinstance(move_lines[0], dict):
                moves_list = []
                for line in move_lines:
                    # Resolve product_id
                    self._get_product_id(line)
                    # Propagate locations if missing
                    if 'location_id' not in line and vals.get('location_id'):
                        line['location_id'] = vals['location_id']
                    if 'location_dest_id' not in line and vals.get('location_dest_id'):
                        line['location_dest_id'] = vals['location_dest_id']
                    # Ensure name is set (required by stock.move)
                    if 'name' not in line and 'product_id' in line:
                         # Fallback to a placeholder if name missing, though caller should provide it
                         line['name'] = 'Move' 
                    moves_list.append((0, 0, line))
                vals['move_ids'] = moves_list
                if 'move_lines' in vals:
                    del vals['move_lines']

        return self.env['stock.picking'].create(vals)

    @api.model
    def create_picking_move(self, vals):
        """
        Create Stock Move (stock.move) inside a picking.
        """
        vals = self._get_product_id(vals)
        return self.env['stock.move'].create(vals)


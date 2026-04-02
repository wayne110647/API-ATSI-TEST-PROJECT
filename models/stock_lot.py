from odoo import models, fields


class StockLot(models.Model):
    _inherit = 'stock.lot'
    warranty = fields.Integer(string='จำนวนปีรับประกัน')
    department = fields.Many2one('hr.department', string='แผนก')
    owner = fields.Many2one('hr.employee', string='ผู้รับผิดชอบ')


class Product_tamplate(models.Model):
    _inherit = 'product.template'
    model = fields.Char(string='รุ่น')
    brand = fields.Char(string='ยี่ห้อ')
    # ram = fields.Char(string='แรม')
    # hdd = fields.Char(string='ฮาร์ดดิส')
    # cpu = fields.Char(string='cpu')

# class InventoryLines(models.Model):
#     """A line of inventory"""
#
#     _inherit = "stock.inventory.line"
#     checkid = fields.Char(string='checkid',default = 'f')

# class Inventory(models.Model):
#     """inventory"""
#
#     _inherit = "stock.inventory"
#     locationis = fields.Many2one('stock.location',string='locationis')
#




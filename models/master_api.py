from odoo import models, api, _

class MasterApi(models.AbstractModel):
    _name = 'master.api'
    _description = 'Master Data Creation API Helper'

    @api.model
    def create_customer(self, vals):
        """
        Create a Customer (res.partner).
        Required in vals: 'name'
        """
        # Ensure it's treated as a customer
        vals['customer_rank'] = 1
        return self.env['res.partner'].create(vals)

    @api.model
    def create_vendor(self, vals):
        """
        Create a Vendor (res.partner).
        Required in vals: 'name'
        """
        # Ensure it's treated as a vendor
        vals['supplier_rank'] = 1
        return self.env['res.partner'].create(vals)

    @api.model
    def create_product(self, vals):
        """
        Create a Product (product.template).
        Required in vals: 'name'
        """
        return self.env['product.template'].create(vals)

    @api.model
    def create_employee(self, vals):
        """
        Create an Employee (hr.employee).
        Required in vals: 'name'
        """
        return self.env['hr.employee'].create(vals)

    @api.model
    def create_chart_of_account(self, vals):
        """
        Create a Chart of Account (account.account).
        Required in vals: 'name', 'code', 'account_type'
        """
        return self.env['account.account'].create(vals)

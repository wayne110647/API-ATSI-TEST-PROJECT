from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class MasterApiController(http.Controller):

    def _response(self, result=None, error=None):
        if error:
            return {'status': 'error', 'message': str(error)}
        return {'status': 'success', 'data': result}

        ### post
        ### http://192.168.1.45:8069/master_api/create/employee
        # {
        #     "jasonrpc": 2.0,
        #     "params": {
        #         "name": "นาย สังคม โทรคม"
        #     }
        # }


    @http.route('/master_api/create/employee', type='json', auth='public', methods=['POST'], csrf=False)
    def create_employee(self, **kwargs):
        """
        Create Employee API
        Payload: {"params": {"name": "Employee Name", ...}}
        """
        try:
            record = request.env['master.api'].sudo().create_employee(kwargs)
            return self._response(result={'id': record.id, 'name': record.name})
        except Exception as e:
            _logger.error("Error creating employee: %s", e)
            return self._response(error=e)

        ### post
        ### http://192.168.1.45:8069/master_api/create/product
        # {
        #     "jasonrpc": 2.0,
        #     "params": {
        #         "name": "ปากกาหมึก"
        #     }
        # }

    @http.route('/master_api/create/product', type='json', auth='public', methods=['POST'], csrf=False)
    def create_product(self, **kwargs):
        """
        Create Product API
        Payload: {"params": {"name": "Product Name", ...}}
        """
        try:
            record = request.env['master.api'].sudo().create_product(kwargs)
            return self._response(result={'id': record.id, 'name': record.name})
        except Exception as e:
            _logger.error("Error creating product: %s", e)
            return self._response(error=e)

    ### post
    ### http://192.168.1.45:8069/master_api/create/customer
    # {
    #     "jasonrpc": 2.0,
    #     "params": {
    #         "name": "บริษัท ไอโอที อินโนเวชั่น จำกัด"
    #     }
    # }

    @http.route('/master_api/create/customer', type='json', auth='public', methods=['POST'], csrf=False)
    def create_customer(self, **kwargs):
        """
        Create Customer API
        Payload: {"params": {"name": "Customer Name", ...}}
        """
        try:
            record = request.env['master.api'].sudo().create_customer(kwargs)
            return self._response(result={'id': record.id, 'name': record.name})
        except Exception as e:
            _logger.error("Error creating customer: %s", e)
            return self._response(error=e)
    ### post
    ### http://192.168.1.45:8069/master_api/create/vendor
    # {
    #     "jasonrpc": 2.0,
    #     "params": {
    #         "name": "บริษัท ไทยยูเนียล จำกัด"
    #     }
    # }

    @http.route('/master_api/create/vendor', type='json', auth='public', methods=['POST'], csrf=False)
    def create_vendor(self, **kwargs):
        """
        Create Vendor API
        Payload: {"params": {"name": "Vendor Name", ...}}
        """
        try:
            record = request.env['master.api'].sudo().create_vendor(kwargs)
            return self._response(result={'id': record.id, 'name': record.name})
        except Exception as e:
            _logger.error("Error creating vendor: %s", e)
            return self._response(error=e)

    ### post
    # head: Content-Type : application/json
    ### http://192.168.1.45:8069/master_api/create/coa
    # {
    #     "jasonrpc": 2.0,
    #     "params": {
    #         "name": "ธนาคาร ไทยพาณิชย์ จำกัด(มหาชน)", "code": "100101"
    #     }
    # }


    @http.route('/master_api/create/coa', type='json', auth='public', methods=['POST'], csrf=False)
    def create_coa(self, **kwargs):
        """
        Create Chart of Account API
        Payload: {"params": {"name": "Account Name", "code": "1001", "account_type": "asset_receivable", ...}}
        """
        try:
            record = request.env['master.api'].sudo().create_chart_of_account(kwargs)
            # account.account might display_name differently
            return self._response(result={'id': record.id, 'name': record.name, 'code': record.code})
        except Exception as e:
            _logger.error("Error creating chart of account: %s", e)
            return self._response(error=e)

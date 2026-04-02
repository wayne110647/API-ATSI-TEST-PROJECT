from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
import json
import requests


class MyController(http.Controller):
    @http.route('/customer', auth='public', methods=['GET', 'POST'], website=True)
    def customer(self, **kw):
        search_for = kw.get('search_for', 'N/A')
        input_search_name = kw.get('input_search_name', 'N/A')

        domain = []
        if search_for == 'type' and input_search_name:
            domain = [('reference_type', 'ilike', input_search_name)]
        elif search_for == 'namespace' and input_search_name:
            domain = [('name', 'ilike', f'%{input_search_name}%')]

        # ค้นหาข้อมูลตามเงื่อนไข
        custs = request.env['main.data'].sudo().search(domain)

        return http.request.render('web_api.index', {
            # 'custs': custs,
            'search_for': search_for,
            'input_search_name': input_search_name,
        })

    @http.route('/customer/add', auth='public', methods=['POST'], csrf=False, website=True)
    def customer_add(self, **kw):
        search_for = kw.get('search_for', False)
        name_search = kw.get('input_search_name', False)
        id_search = kw.get('id_search', False)
        web_id = kw.get('id')  # รับ id จาก URL
        # web_id = request.params.get('id')

        domain = []
        if search_for == 'type' and name_search:
            domain = [('reference_type', 'ilike', name_search)]
        elif search_for == 'namespace' and name_search:
            domain = [('name', 'ilike', f'%{name_search}%')]

        # ค้นหาข้อมูลใน main.data ตาม domain
        data_id = request.env['main.data'].search(domain)

        if data_id:
            # สร้างบันทึกใน search.engine.line
            for line in data_id:
                values = {
                    'name': line.id,
                    'type': line.reference_type,
                    'description': line.description,
                    'mult': line.mult,
                }
                request.env['search.engine.line'].create(values)

            # ส่งข้อมูลที่ค้นหาไปยังเทมเพลต
            return request.render('web_api.index', {
                'custs': data_id,
                'input_search_name': name_search,
                'id_search': web_id,  # ส่ง id ของหน้าเว็บไปยัง template
            })

        return request.redirect(f'/customer/add?id={id_search}')

    @http.route('/customer/search_log', auth='public', methods=['GET'], csrf=False)
    def search_log(self, **kwargs):
        web_id = kwargs.get('id')

        if not web_id:
            return request.make_response('web_id is required', status=400)

        # ค้นหาใน search.log โดยใช้ web_id
        log_record = request.env['search.log'].search([('id', '=', web_id)], limit=1)

        if log_record:
            # ดึงค่า search_for และ name_search
            search_for = log_record.search_for
            name_search = log_record.name_search

            # สร้าง domain สำหรับค้นหาใน main.data
            domain = []
            if search_for == 'type' and name_search:
                domain = [('reference_type', 'ilike', name_search)]
            elif search_for == 'namespace' and name_search:
                domain = [('name', 'ilike', f'%{name_search}%')]

            # ค้นหาใน main.data
            data_id = request.env['main.data'].search(domain)

            # หากมีข้อมูลใน main.data
            if data_id:
                # สร้างบันทึกใน search.engine.line
                for line in data_id:
                    values = {
                        'name': line.id,
                        'type': line.reference_type,
                        'description': line.description,
                        'mult': line.mult,
                    }
                    request.env['search.engine.line'].create(values)

                # รีไดเรกต์ไปยัง /customer/add พร้อมกับ id ของ log_record
                return request.redirect(f'/customer/add?id={log_record.id}')
            else:
                return request.make_response('No data found in main.data', status=404)
        else:
            return request.make_response('Record not found', status=404)

    @http.route('/customer/edit', auth='public', website=True)
    def customer_edit(self):
        id = request.params.get('id')
        print('id=', id)
        data_id = request.env['res.partner'].sudo().search([('id', '=', id)])
        print('data=', data_id)
        return http.request.render('web_api.customer_edit', {'data': data_id})

    @http.route('/customer/update', auth='public', methods=['POST'], csrf=False, website=True)
    def product_update(self, **kw):

        http.request.env['res.partner'].search([('id', '=', kw.get('txt_id'))]).sudo().write({
            'name': kw['txt_name'],
            'street': kw['txt_street'],

        })
        print(kw['txt_name'])

    @http.route('/customer/delete', auth='public', csrf=False, website=True)
    def customer_delete(self, **kw):
        id = request.params.get('id')
        http.request.env['res.partner'].search([('id', '=', id)]).sudo().unlink()
        # print(kw['txt_name'])

    @http.route('/detail', auth='public', website=True)
    def detail_show(self, **kw):
        custs = request.env['res.partner'].sudo().search([])
        return http.request.render('web_api.detail')

    @http.route('/detail/edit', auth='public', website=True)
    def detail_edit(self):
        id = request.params.get('id')
        int_id = int(id)
        # print('id=', id)
        data_id = request.env['attribute.detail'].sudo().search([('name', '=', int_id)])
        main_data_id = request.env['main.data'].sudo().search([('id', '=', int_id)])
        # print('data=', data_id)

        return http.request.render('web_api.detail', {
            'data': data_id,
            'main_data': main_data_id
        })

    ################################### Start Stock Operation #################################################


    @http.route('/api/chk_barcode', type="json", auth='public', methods=['POST'])
    def chk_barcode(self):
        data = http.request.params

        # Validate input
        barcode = data.get('barcode')
        try:
            # ค้นหาประเภทการ picking ที่มี sequence_code เป็น 'in'
            product = request.env['product.product'].sudo().search([
                ('barcode', '=', barcode)
            ])
            product_tml_id = product.product_tmpl_id.id
            get_rec01 = request.env['product.template'].sudo().search([('id', '=', product_tml_id)])
            p_name = get_rec01.name
            p_model = get_rec01.model
            p_brand = get_rec01.brand
            # p_ram = get_rec01.ram
            # p_hdd = get_rec01.hdd
            # p_cpu = get_rec01.cpu
            return {
                'name': p_name,
                'model': p_model,
                'brand': p_brand,
                # 'ram': p_ram,
                # 'hdd': p_ram,
                # 'cpu': p_cpu,
                'id': product.id,
                'message': 'Found',
            }

        except Exception as e:
            # การจัดการข้อผิดพลาด
            return {'error': str(e)}

    @http.route('/check_pin', type="json", auth='public', methods=['POST'], csrf=False)
    def check_pin(self):
        data = http.request.params
        if not data['pin']:
            raise Exception("Parameter pin not found.")

        # get all teachers
        get_rec = request.env['hr.employee'].sudo().search([('pin', '=', data['pin'])], limit=1, order="id desc")
        res_msg = []
        for rec in get_rec:
            res_msg.append({
                'id': rec.id,
                'code': rec.emp_id,
                'message': 'found',

            })
        if not res_msg:
            res_msg.append({
                'id': 'NO',
                'code': 'NO',
                'message': 'NO',
            })
        return res_msg

    @http.route('/api/get_ponumber', type="json", auth='public', methods=['POST'])
    def get_ponumber(self):
        try:
            # ค้นหาประเภทการ picking ที่มี sequence_code เป็น 'in'
            picking_types = request.env['stock.picking.type'].sudo().search([
                ('sequence_code', '=', 'IN')
            ])

            # ดึง IDs ของ picking types ที่ตรงกับเงื่อนไข
            picking_type_ids = picking_types.mapped('id')

            # ค้นหาข้อมูล stock.picking ที่มีสถานะเป็น 'assigned', origin ไม่ว่าง, และ picking_type ตรงกับที่ค้นหา
            locations = request.env['stock.picking'].sudo().search([
                ('state', '=', 'assigned'),
                ('origin', '!=', False),  # ตรวจสอบว่า origin ไม่เป็น False หรือว่าง
                ('picking_type_id', 'in', picking_type_ids)  # ตรวจสอบว่า picking_type ตรงกับที่ค้นหา
            ])

            # คืนค่าข้อมูลในรูปแบบที่ต้องการ
            return [{'id': loc.id, 'name': loc.origin} for loc in locations]
        except Exception as e:
            # การจัดการข้อผิดพลาด
            return {'error': str(e)}

    ################################ START New Stock Rective  ############################################################
    ######## Get Whouse Line IN ok
    @http.route('/get_list_whin', type='json', auth='public', methods=['GET'], csrf=False, website=True)
    def get_list_stockin(self, **kw):
        #http://localhost:8069/get_list_whin
        # {

        # }
        try:
            domain = [('state', '=', 'assigned'), ('location_dest_id', '=', 8)]
            stockin_records = request.env['stock.picking'].sudo().search(domain)
            result = [{'code': rec.name, 'po': rec.origin} for rec in stockin_records]
            return result  # ✅ return ตรง ๆ
        except Exception as e:
            return {'error': str(e)}
    ######## Get PO Detail ok
    @http.route('/get_list_po', type='json', auth='public', methods=['POST'], csrf=False, website=True)
    def get_list_podtl(self, **kw):
        #http://localhost:8069/get_list_po
        # {
        #     "jasonrpc": 2.0,
        #     "params": {
        #         "po_name": "P00006"
        #
        #     }
        # }
        try:
            po_name = kw.get('po_name')
            if not po_name:
                return {'error': 'Missing parameter: po_name'}

            query = """
                SELECT pol.name, pol.product_qty
                FROM purchase_order po
                INNER JOIN purchase_order_line pol ON po.id = pol.order_id
                WHERE po.name = %s
            """
            request.env.cr.execute(query, (po_name,))
            rows = request.env.cr.fetchall()

            result = [{'line_name': r[0], 'qty': r[1]} for r in rows]
            return result
        except Exception as e:
            return {'error': str(e)}

    ######## receive by lot

    @http.route('/stock_receive_lot', type="json", auth='public', methods=['POST'], csrf=False, website=True)
    def stock_receive_lot(self, **kwargs):
        # รับค่า params จาก body request
        # http://localhost:8069/stock_receive_lot
        # {
        #     "jasonrpc": 2.0,
        #     "params": {
        #         "po": "P00008",
        #         "barcode": "P-02-Aurea",
        #         "lot_no": "Lot-25-08-06-P02-001",
        #         "received_qty": 5
        #
        #     }
        # }
        data = http.request.params

        # ดึงค่าจาก params
        po_no = data['po']  # รับค่า  po no
        barcode = data['barcode']  # รับค่า productName เป็น barcode
        lot_no = data['lot_no']  # รับค่า lot no
        received_qty = data['received_qty']  # รับค่า receivedQty
        ## find product_id
        rec = request.env['product.product'].sudo().search([('barcode', '=', barcode)])
        if rec:
            product_id = rec.id
            tmpl_id = rec.product_tmpl_id.id
            rec01 = request.env['product.template'].sudo().search([('id', '=', tmpl_id)])
            product_uom_id = rec01.uom_id.id

        # ค้นหาข้อมูลจาก stock.picking โดยตรง

        stock_pickings = request.env['stock.picking'].sudo().search([('origin', '=', po_no)])

        picking_id = stock_pickings.id
        stock_move = request.env['stock.move'].sudo().search(
            [('picking_id', '=', picking_id), ('product_id', '=', product_id)])
        location_dest_id = stock_move.location_dest_id.id
        location_id = stock_move.location_id.id
        # สร้าง lot no
        lot_id = request.env['stock.lot'].sudo().create({
            'product_id': product_id,
            'product_uom_id': product_uom_id,
            'name': lot_no,
            'location_id': location_dest_id,
            'company_id': 1,

        })
        # location 4 from
        in_date = datetime.now()
        tinventory_diff_quantity =  received_qty
        quantity = (-1) * received_qty
        request.env['stock.quant'].sudo().create({
            'product_id': product_id,
            'location_id': location_id,
            'lot_id': lot_id.id,
            'quantity': quantity,
            'inventory_diff_quantity': tinventory_diff_quantity,
            'in_date': in_date,
        })
        # location 8 dest

        tinventory_diff_quantity = (-1) * received_qty
        quantity =   received_qty
        request.env['stock.quant'].sudo().create({
            'product_id': product_id,
            'location_id': location_dest_id,
            'lot_id': lot_id.id,
            'quantity': quantity,
            'inventory_diff_quantity': tinventory_diff_quantity,
            'in_date': in_date,
        })

        # ค้นหาข้อมูลใน stock.move.line ที่มีการเชื่อมโยงกับ stock.picking
        for picking in stock_pickings:
            # ค้นหาข้อมูลจาก stock.move.line ที่มี picking_id ตรงกับ stock.picking
            move_lines = request.env['stock.move.line'].sudo().search([('picking_id', '=', picking.id)])

            for move_line in move_lines:
                # ตรวจสอบว่า barcode และ lot number ตรงกับที่ได้รับมาหรือไม่
                # ทำการอัปเดตค่า lot_name และ qty_done
                move_line.write({
                    'state' :'done',
                    'lot_id': lot_id,  # อัปเดต lot_id หากมีการเปลี่ยนแปลง
                    'lot_name': lot_no,
                    'company_id': 1,
                    'picked':True
                })

                # ทำการ Update table purchase_order_line set qty_received = จำนวน SN ที่ยิงรับเข้า อ่านค่าเก่าแล้วบวกเพิ่ม 1
        rec07 = request.env['purchase.order'].sudo().search([('name', '=', po_no)])
        order_id = rec07.id
        rec08 = request.env['purchase.order.line'].sudo().search(
            [('order_id', '=', order_id), ('product_id', '=', product_id)])
        purchase_id_line = rec08.id
        product_qty = rec08.product_qty
        updata = {
            'qty_received': received_qty,
            'state' : 'done',
        }
        rec08.sudo().write(updata)

        state = {
            'state' : 'done',
        }
        stock_pickings.sudo().write(state)

        stock_move.sudo().write(state)
        # ส่งผลลัพธ์กลับไป

        return json.dumps({'status': 'success'})

    ######## receive by barcode

    @http.route('/stock_receive_barcode', type="json", auth='public', methods=['POST'], csrf=False, website=True)
    def stock_receive_barcode(self, **kwargs):
        # รับค่า params จาก body request
        # http://localhost:8069/stock_receive_barcode
        # {
        #     "jasonrpc": 2.0,
        #     "params": {
        #         "po": "P00008",
        #         "barcode": "P-01-Apollo",
        #         "received_qty": 5
        #
        #     }
        # }
        data = http.request.params

        # ดึงค่าจาก params
        po_no = data['po']  # รับค่า  po no
        barcode = data['barcode']  # รับค่า productName เป็น barcode
        received_qty = data['received_qty']  # รับค่า receivedQty
        ## find product_id
        rec = request.env['product.product'].sudo().search([('barcode', '=', barcode)])
        if rec:
            product_id = rec.id
            tmpl_id = rec.product_tmpl_id.id
            rec01 = request.env['product.template'].sudo().search([('id', '=', tmpl_id)])
            product_uom_id = rec01.uom_id.id

        # ค้นหาข้อมูลจาก stock.picking โดยตรง

        stock_pickings = request.env['stock.picking'].sudo().search([('origin', '=', po_no)])

        picking_id = stock_pickings.id
        stock_move = request.env['stock.move'].sudo().search(
            [('picking_id', '=', picking_id), ('product_id', '=', product_id)])
        location_dest_id = stock_move.location_dest_id.id
        location_id = stock_move.location_id.id


        # ค้นหาข้อมูลใน stock.move.line ที่มีการเชื่อมโยงกับ stock.picking
        for picking in stock_pickings:
            # ค้นหาข้อมูลจาก stock.move.line ที่มี picking_id ตรงกับ stock.picking
            move_lines = request.env['stock.move.line'].sudo().search([('picking_id', '=', picking.id)])

            for move_line in move_lines:
                # ตรวจสอบว่า barcode และ lot number ตรงกับที่ได้รับมาหรือไม่
                # ทำการอัปเดตค่า lot_name และ qty_done
                move_line.write({
                    'state' :'done',
                    # 'lot_id': lot_id,  # อัปเดต lot_id หากมีการเปลี่ยนแปลง
                    # 'lot_name': lot_no,
                    'company_id': 1,
                    'picked':True
                })

                # ทำการ Update table purchase_order_line set qty_received = จำนวน SN ที่ยิงรับเข้า อ่านค่าเก่าแล้วบวกเพิ่ม 1
        rec07 = request.env['purchase.order'].sudo().search([('name', '=', po_no)])
        order_id = rec07.id
        rec08 = request.env['purchase.order.line'].sudo().search(
            [('order_id', '=', order_id), ('product_id', '=', product_id)])
        purchase_id_line = rec08.id
        product_qty = rec08.product_qty
        updata = {
            'qty_received': received_qty,
            'state' : 'done',
        }
        rec08.sudo().write(updata)
        in_date = datetime.now()
        #### Update stock quant by barcode read old qty + received_qty location 8 whstock
        rec09 = request.env['stock.quant'].sudo().search(
            [('location_id', '=', 8), ('product_id', '=', product_id)])
        onhand = rec09.quantity
        balance = onhand + received_qty
        if rec09:
            updata_qty = {
                'quantity': balance,
                'reserved_quantity': balance,
            }
            rec09.sudo().write(updata_qty)
        else:
            request.env['stock.quant'].sudo().create({
                'product_id': product_id,
                'location_id': 8,  # to
                'quantity': received_qty,  # ลบออก
                'inventory_diff_quantity': -1 * received_qty,
                'in_date': in_date,
            })

        state = {
            'state' : 'done',
        }
        stock_pickings.sudo().write(state)
        stock_move.sudo().write(state)
        # ส่งผลลัพธ์กลับไป

        return json.dumps({'status': 'success'})

    ######## receive by lot

    @http.route('/stock_receive_sn', type="json", auth='public', methods=['POST'], csrf=False, website=True)
    def stock_receive_serial(self, **kwargs):
        # รับค่า params จาก body request
        # {
        #     "jsonrpc": "2.0",
        #     "method": "call",
        #     "params": {
        #         "po": "P00008",
        #         "barcode": "P-03-Ember",
        #         "sn_no": [
        #             "SN-25-08-06-P03-001",
        #             "SN-25-08-06-P03-002",
        #             "SN-25-08-06-P03-003"
        #         ],
        #         "received_qty": 3
        #     }
        # }
        data = http.request.params

        # ดึงค่าจาก params
        po_no = data['po']  # รับค่า  po no
        barcode = data['barcode']  # รับค่า productName เป็น barcode
        lot_no = data.get('sn_no', [])  # sn_no จะเป็น list
        received_qty = data['received_qty']  # รับค่า receivedQty
        ## find product_id
        rec = request.env['product.product'].sudo().search([('barcode', '=', barcode)])
        if rec:
            product_id = rec.id
            tmpl_id = rec.product_tmpl_id.id
            rec01 = request.env['product.template'].sudo().search([('id', '=', tmpl_id)])
            product_uom_id = rec01.uom_id.id

        # ค้นหาข้อมูลจาก stock.picking โดยตรง

        stock_pickings = request.env['stock.picking'].sudo().search([('origin', '=', po_no)])

        picking_id = stock_pickings.id
        stock_move = request.env['stock.move'].sudo().search(
            [('picking_id', '=', picking_id), ('product_id', '=', product_id)])
        location_dest_id = stock_move.location_dest_id.id
        location_id = stock_move.location_id.id
        # สร้าง loop create lot no
        array_lot_id = []  # สร้างลิสต์ว่างไว้ก่อน
        for lot in lot_no:
            lot_id = request.env['stock.lot'].sudo().create({
                'product_id': product_id,
                'product_uom_id': product_uom_id,
                'name': lot,
                'location_id': location_dest_id,
                'company_id': 1,
            })
            array_lot_id.append(lot_id.id)  # หรือจะเก็บเป็น lot_id.name ก็ได้

        # location 4 = from / location 8 = dest
        in_date = datetime.now()

        for lot_id in array_lot_id:
            # จาก location ต้นทาง (ออกของ)
            request.env['stock.quant'].sudo().create({
                'product_id': product_id,
                'location_id': location_id,  # from
                'lot_id': lot_id,
                'quantity': -1,  # ลบออก
                'inventory_diff_quantity': 1,
                'in_date': in_date,
            })

            # ไปยัง location ปลายทาง (รับของ)
            request.env['stock.quant'].sudo().create({
                'product_id': product_id,
                'location_id': location_dest_id,  # to
                'lot_id': lot_id,
                'quantity': 1,  # เพิ่มเข้า
                'inventory_diff_quantity': -1,
                'in_date': in_date,
            })

        # ค้นหาข้อมูลใน stock.move.line ที่มีการเชื่อมโยงกับ stock.picking
        # สมมติว่า lot_no และ lot_id จับคู่กันตาม index (ตำแหน่งใน list)
        lot_pair = list(zip(lot_no, array_lot_id))

        for picking in stock_pickings:
            move_lines = request.env['stock.move.line'].sudo().search([
                ('picking_id', '=', picking.id),
                ('product_id', '=', product_id),
            ])

            for idx, move_line in enumerate(move_lines):
                if idx < len(lot_pair):  # ป้องกัน index เกิน
                    lot_name, lot_id = lot_pair[idx]
                    move_line.write({
                        'lot_id': lot_id,
                        'lot_name': lot_name,
                        # 'qty_done': 1,  # เพิ่มของ 1 ชิ้น (หรือมากกว่านี้ถ้าเป็นกลุ่ม)
                        'company_id': request.env.company.id,
                        'picked': True
                    })

                # ทำการ Update table purchase_order_line set qty_received = จำนวน SN ที่ยิงรับเข้า อ่านค่าเก่าแล้วบวกเพิ่ม 1
        rec07 = request.env['purchase.order'].sudo().search([('name', '=', po_no)])
        order_id = rec07.id
        rec08 = request.env['purchase.order.line'].sudo().search(
            [('order_id', '=', order_id), ('product_id', '=', product_id)])
        purchase_id_line = rec08.id
        product_qty = rec08.product_qty
        updata = {
            'qty_received': received_qty,
            'state' : 'done',
        }
        rec08.sudo().write(updata)

        state = {
            'state' : 'done',
        }
        stock_pickings.sudo().write(state)

        stock_move.sudo().write(state)
        # ส่งผลลัพธ์กลับไป

        return json.dumps({'status': 'success'})

    ################################ END New Stock Rective  #####
    ################################ START New Stock Issue  ############################################################
    ######## Get Whouse Line OUT ok
    @http.route('/get_list_whout', type='json', auth='public', methods=['GET'], csrf=False, website=True)
    def get_list_stockout(self, **kw):
        #http://localhost:8069/get_list_whout
        # {

        # }
        try:
            domain = [('state', '!=', 'done'), ('location_dest_id', '=', 5)]
            stockin_records = request.env['stock.picking'].sudo().search(domain)
            result = [{'code': rec.name, 'so': rec.origin} for rec in stockin_records]
            return result  # ✅ return ตรง ๆ
        except Exception as e:
            return {'error': str(e)}
    ######## Get SO Detail ok
    @http.route('/get_list_so', type='json', auth='public', methods=['POST'], csrf=False, website=True)
    def get_list_sodtl(self, **kw):
        #http://localhost:8069/get_list_so
        # {
        #     "jasonrpc": 2.0,
        #     "params": {
        #         "so_name": "S00009"
        #
        #     }
        # }
        try:
            so_name = kw.get('so_name')
            if not so_name:
                return {'error': 'Missing parameter: so_name'}

            query = """
                SELECT sol.name, sol.product_uom_qty
                FROM sale_order so
                INNER JOIN sale_order_line sol ON so.id = sol.order_id
                WHERE so.name = %s
            """
            request.env.cr.execute(query, (so_name,))
            rows = request.env.cr.fetchall()

            result = [{'line_name': r[0], 'qty': r[1]} for r in rows]


            return result
        except Exception as e:
            return {'error': str(e)}

    ######## Issue by lot

    @http.route('/stock_issue_lot', type="json", auth='public', methods=['POST'], csrf=False, website=True)

    def stock_issue_lot(self, **kwargs):
        # http://localhost:8069/stock_issue_lot
        # {
        #     "jsonrpc": "2.0",
        #     "params": {
        #         "so": "S00027",
        #         "barcode": "P-02-Aurea",
        #         "lot_no": [
        #             ["Lot-25-08-12-P02-001", 10],
        #             ["Lot-25-08-12-P02-002", 8],
        #             ["Lot-25-08-12-P02-003", 2]
        #
        #         ],
        #         "issue_qty": 20
        #     }
        # }

        data = http.request.params
        so_no = data.get('so')
        barcode = data.get('barcode')
        lot_no_list = data.get('lot_no', [])  # [['lot1', qty1], ['lot2', qty2], ...]
        issue_qty = data.get('issue_qty')

        rec = request.env['product.product'].sudo().search([('barcode', '=', barcode)], limit=1)
        if not rec:
            return {"error": "Product not found"}

        product_id = rec.id
        tmpl_id = rec.product_tmpl_id.id
        rec01 = request.env['product.template'].sudo().browse(tmpl_id)
        product_uom_id = rec01.uom_id.id

        picking = request.env['stock.picking'].sudo().search([('origin', '=', so_no)], limit=1)
        if not picking:
            return {"error": "Stock Picking not found"}

        # ทำการ Update table sale_order_line set qty_delivered = จำนวน issue
        rec07 = request.env['sale.order'].sudo().search([('name', '=', so_no)])
        order_id = rec07.id
        rec08 = request.env['sale.order.line'].sudo().search(
            [('order_id', '=', order_id), ('product_id', '=', product_id)])

        updata = {
            'qty_delivered': issue_qty,
        }
        rec08.sudo().write(updata)

        move = request.env['stock.move'].sudo().search([
            ('picking_id', '=', picking.id),
            ('product_id', '=', product_id),
            ('sale_line_id', '=', rec08.id)
        ], limit=1)
        location_id = move.location_id.id
        location_dest_id = move.location_dest_id.id
        if not move:
            return {"error": "Stock Move not found"}
        del_line = request.env['stock.move.line'].sudo().search([
            ('move_id', '=', move.id),
            ('picking_id', '=', picking.id),
            ('product_id', '=', product_id),
            ('state', '=', 'assigned'),
        ], )
        if del_line:
            del_line.unlink()
            
        in_date = datetime.now()
        for lot_name, lot_qty in lot_no_list:
            lot = request.env['stock.lot'].sudo().search([
                ('name', '=', lot_name),
                ('product_id', '=', product_id)
            ], limit=1)

            if not lot:
                return {"error": f"Lot {lot_name} not found"}

            quant = request.env['stock.quant'].sudo().search([
                ('product_id', '=', product_id),
                ('lot_id', '=', lot.id),
                ('location_id', '=', location_id),
            ], limit=1)

            if not quant:
                return {"error": f"Quant for lot {lot_name} not found"}

            new_qty = quant.quantity - lot_qty
            quant.write({'quantity': new_qty})

            move_line = request.env['stock.move.line'].sudo().search([
                ('move_id', '=', move.id),
                ('picking_id', '=', picking.id),
                ('product_id', '=', product_id),
                ('lot_id', '=', lot.id),
                ('state', '=', 'assigned'),
            ], )
            if not move_line:
                # return {"error": "Product not found"}
                # create move_line
                request.env['stock.move.line'].sudo().create({
                    'picking_id': picking.id,
                    'move_id': move.id,
                    'company_id': 1,
                    'product_id': product_id,
                    'product_uom_id': 1,
                    'lot_id': lot.id,
                    'location_id':  location_id,
                    'location_dest_id': location_dest_id,
                    'product_category_name': 'All',
                    'state':'done',
                    'reference': move.reference,
                    'quantity': lot_qty,  # เพิ่มเข้า
                    'quantity_product_uom': lot_qty,
                    'date': in_date,
                })

            else:
                upd_mvl = {
                    'lot_id': lot.id,
                    'quantity': lot_qty,
                    'quantity_product_uom': lot_qty,
                    'state': 'done',
                }
                move_line.write(upd_mvl)


        state = {
            'state' : 'done',
        }
        picking.sudo().write(state)

        move.sudo().write(state)
        # ส่งผลลัพธ์กลับไป

        return json.dumps({'status': 'success'})

    # ######## receive by barcode
    #
    @http.route('/stock_issue_barcode', type="json", auth='public', methods=['POST'], csrf=False, website=True)
    def stock_issue_barcode(self, **kwargs):
        # รับค่า params จาก body request
        # http://localhost:8069/stock_issue_barcode
        # {
        #     "jasonrpc": 2.0,
        #     "params": {
        #         "so": "S00019",
        #         "barcode": "P-01-Apollo",
        #         "issue_qty": 50
        #
        #     }
        # }
        data = http.request.params

        # ดึงค่าจาก params
        so_no = data['so']  # รับค่า  po no
        barcode = data['barcode']  # รับค่า productName เป็น barcode
        issue_qty = data['issue_qty']  # รับค่า receivedQty
        ## find product_id
        rec = request.env['product.product'].sudo().search([('barcode', '=', barcode)])
        if rec:
            product_id = rec.id
            tmpl_id = rec.product_tmpl_id.id
            rec01 = request.env['product.template'].sudo().search([('id', '=', tmpl_id)])
            product_uom_id = rec01.uom_id.id

        # ค้นหาข้อมูลจาก stock.picking โดยตรง

        stock_pickings = request.env['stock.picking'].sudo().search([('origin', '=', so_no)])

        picking_id = stock_pickings.id
        stock_move = request.env['stock.move'].sudo().search(
            [('picking_id', '=', picking_id), ('product_id', '=', product_id)])
        location_dest_id = stock_move.location_dest_id.id
        location_id = stock_move.location_id.id

        in_date = datetime.now()
        # ค้นหาข้อมูลใน stock.move.line ที่มีการเชื่อมโยงกับ stock.picking
        for picking in stock_pickings:
            # ค้นหาข้อมูลจาก stock.move.line ที่มี picking_id ตรงกับ stock.picking
            #move_lines = request.env['stock.move.line'].sudo().search([('picking_id', '=', picking.id)])

            # create move line *************************
            request.env['stock.move.line'].sudo().create({
                'picking_id': picking.id,
                'move_id': stock_move.id,
                'company_id': 1,
                'product_id': product_id,
                'product_uom_id': 1,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'product_category_name': 'All',
                'state': 'done',
                'reference': stock_move.reference,
                'quantity': issue_qty,  # เพิ่มเข้า
                'quantity_product_uom': issue_qty,
                'date': in_date,
            })
                # ทำการ Update table purchase_order_line set qty_received = จำนวน SN ที่ยิงรับเข้า อ่านค่าเก่าแล้วบวกเพิ่ม 1
        rec07 = request.env['sale.order'].sudo().search([('name', '=', so_no)])
        order_id = rec07.id
        rec08 = request.env['sale.order.line'].sudo().search(
            [('order_id', '=', order_id), ('product_id', '=', product_id)])
        purchase_id_line = rec08.id
        #product_qty = rec08.product_qty
        updata = {
            'qty_delivered': issue_qty,
           # 'state' : 'done',
        }
        rec08.sudo().write(updata)

        #### Update stock quant by barcode read old qty + received_qty location 8 whstock
        rec09 = request.env['stock.quant'].sudo().search(
            [('location_id', '=', 8), ('product_id', '=', product_id)])
        onhand = rec09.quantity
        balance = onhand - issue_qty
        updata_qty = {
            'quantity': balance,
            'reserved_quantity': balance,
        }
        rec09.sudo().write(updata_qty)

        state = {
            'state' : 'done',
        }
        stock_pickings.sudo().write(state)
        move_upd = {
            'state' : 'done',
            'quantity': issue_qty,
        }
        stock_move.sudo().write(move_upd)
        # ส่งผลลัพธ์กลับไป

        return json.dumps({'status': 'success'})

    # ######## issue by serial

    @http.route('/stock_issue_sn', type="json", auth='public', methods=['POST'], csrf=False, website=True)
    def stock_issue_serial(self, **kwargs):
        # รับค่า params จาก body request
        # http://localhost:8069/stock_issue_sn
        # {
        #     "jsonrpc": "2.0",
        #     "method": "call",
        #     "params": {
        #         "so": "S00024",
        #         "barcode": "P-03-Ember",
        #         "sn_no": [
        #             "SN-25-08-06-P03-005",
        #             "SN-25-08-06-P03-006",
        #             "SN-25-08-06-P03-007",
        #             "SN-25-08-06-P03-011",
        #            "SN-25-08-06-P03-012",
        #         ],
        #         "issue_qty": 5
        #     }
        # }
        data = http.request.params

        # ดึงค่าจาก params
        so_no = data['so']  # รับค่า  po no
        barcode = data['barcode']  # รับค่า productName เป็น barcode
        lot_no = data.get('sn_no', [])  # sn_no จะเป็น list
        issue_qty = data['issue_qty']  # รับค่า receivedQty
        ## find product_id
        rec = request.env['product.product'].sudo().search([('barcode', '=', barcode)])
        if rec:
            product_id = rec.id
            tmpl_id = rec.product_tmpl_id.id
            rec01 = request.env['product.template'].sudo().search([('id', '=', tmpl_id)])
            product_uom_id = rec01.uom_id.id

        # ค้นหาข้อมูลจาก stock.picking โดยตรง

        stock_pickings = request.env['stock.picking'].sudo().search([('origin', '=', so_no)])

        picking_id = stock_pickings.id
        stock_move = request.env['stock.move'].sudo().search(
            [('picking_id', '=', picking_id), ('product_id', '=', product_id)])
        location_dest_id = stock_move.location_dest_id.id
        location_id = stock_move.location_id.id

        # สร้าง loop create lot no
        array_lot_id = []  # สร้างลิสต์ว่างไว้ก่อน
        for lot in lot_no:
            lot_id = request.env['stock.lot'].sudo().search([('name', '=', lot)])
            array_lot_id.append(lot_id.id)  # หรือจะเก็บเป็น lot_id.name ก็ได้
        # Update for localtion 8 quantity=0 ,reserved_quantity= 0
        #and create for location_dest_id 5 quantity=1 ,reserved_quantity= 0 ,inventory_diff_quantity =-1

        in_date = datetime.now()

        for lot_id in array_lot_id:
            # จาก location ต้นทาง (ออกของ)
            request.env['stock.quant'].sudo().create({
                'product_id': product_id,
                'location_id': location_dest_id,  # to
                'lot_id': lot_id,
                'quantity': 1,  # ลบออก
                'reserved_quantity': 0,
                'inventory_diff_quantity': -1,
                'in_date': in_date,
            })

            #  location ต้นทาง Update Error
            upd_sn = request.env['stock.quant'].sudo().search([('lot_id', '=', lot_id)])
            updata_qty = {
                'quantity': 0,
                'reserved_quantity': 0,
            }
            upd_sn.sudo().write(updata_qty)

        # ค้นหาข้อมูลใน stock.move.line ที่มีการเชื่อมโยงกับ stock.picking
        # สมมติว่า lot_no และ lot_id จับคู่กันตาม index (ตำแหน่งใน list)
        lot_pair = list(zip(lot_no, array_lot_id))
#***********************
        for picking in stock_pickings:
            move_lines = request.env['stock.move.line'].sudo().search([
                ('picking_id', '=', picking.id),
                ('product_id', '=', product_id),
            ])

            for idx, move_line in enumerate(move_lines):
                if idx < len(lot_pair):  # ป้องกัน index เกิน
                    lot_name, lot_id = lot_pair[idx]
                    move_line.write({
                        'lot_id': lot_id,
                        'lot_name': lot_name,
                        'company_id': request.env.company.id,
                        'picked': True,
                        'state': 'done',
                    })

                # ทำการ Update table purchase_order_line set qty_received = จำนวน SN ที่ยิงรับเข้า อ่านค่าเก่าแล้วบวกเพิ่ม 1
        rec07 = request.env['sale.order'].sudo().search([('name', '=', so_no)])
        order_id = rec07.id
        rec08 = request.env['sale.order.line'].sudo().search(
            [('order_id', '=', order_id), ('product_id', '=', product_id)])
        purchase_id_line = rec08.id
        #product_qty = rec08.product_qty
        updata = {
            'qty_delivered': issue_qty,

        }
        rec08.sudo().write(updata)

        state = {
            'state' : 'done',
        }
        stock_pickings.sudo().write(state)

        stock_move.sudo().write(state)
        # ส่งผลลัพธ์กลับไป

        return json.dumps({'status': 'success'})

    ################################ END New Stock Issue  #####
    ################################ Start New Stock Internal Transfer  #####
    # Get List WH/TRN
    @http.route('/get_list_whtrn', type='json', auth='public', methods=['GET'], csrf=False, website=True)
    def get_list_stocktrn(self, **kw):
        #http://localhost:8069//get_list_whtrn
        # {

        # }
        try:
            domain = [('state', '!=', 'done'), ('picking_type_id', '=', 5)]
            stockin_records = request.env['stock.picking'].sudo().search(domain)
            result = [{'code': rec.name} for rec in stockin_records]
            return result  # ✅ return ตรง ๆ
        except Exception as e:
            return {'error': str(e)}

    @http.route('/get_list_trn', type='json', auth='public', methods=['POST'], csrf=False, website=True)
    def get_list_trndtl(self, **kw):
        #http://localhost:8069/get_list_trn
        # {
        #     "jasonrpc": 2.0,
        #     "params": {
        #         "trn_name": "WH/INT/00027"
        #
        #     }
        # }
        try:
            trn_name = kw.get('trn_name')
            if not trn_name:
                return {'error': 'Missing parameter: trn_name'}

            query = """
                SELECT sm.name, sm.product_uom_qty
                FROM stock_move sm                
                WHERE sm.reference =%s
            """
            request.env.cr.execute(query, (trn_name,))
            rows = request.env.cr.fetchall()

            result = [{'line_name': r[0], 'qty': r[1]} for r in rows]


            return result
        except Exception as e:
            return {'error': str(e)}

    @http.route('/get_list_location', type='json', auth='public', methods=['GET'], csrf=False, website=True)
    def get_list_stock_location(self, **kw):
        #http://localhost:8069//get_list_location
        # {

        # }
        try:
            domain = [('usage', '=', 'internal'), ('active', '=', True)]
            stockin_records = request.env['stock.location'].sudo().search(domain)
            result = [{'code': rec.complete_name} for rec in stockin_records]
            return result  # ✅ return ตรง ๆ
        except Exception as e:
            return {'error': str(e)}

    # Transfer By Lot
    @http.route('/set_tranfer_location_lot', type='json', auth='public', methods=['POST'], csrf=False, website=True)
    def set_tranfer_location_lot(self, **kw):
        # http://localhost:8069/set_tranfer_location_lot
        # {
        #     "jsonrpc": "2.0",
        #     "params": {
        #         "code": "WH/INT/00004",
        #         "barcode": "P-02-Aurea",
        #         "lot_no": [
        #             ["Lot-25-08-12-P02-001", 4],
        #             ["Lot-25-08-12-P02-003", 6]
        #
        #         ],
        #          "location_from": "WH/สต็อก",
        #          "location_to": "WH1/Stock/WH1/LocationA",
        #         "transfer_qty": 10
        #     }
        # }

        data = http.request.params
        code = data.get('code')
        barcode = data.get('barcode')
        lot_no_list = data.get('lot_no', [])  # [['lot1', qty1], ['lot2', qty2], ...]
        location_from = data.get('location_from')
        location_to = data.get('location_to')
        transfer_qty = data.get('transfer_qty')

        locfrom = [('usage', '=', 'internal'), ('active', '=', True), ('complete_name', '=', location_from)]
        locationid_from = request.env['stock.location'].sudo().search(locfrom)
        locfrom_id =  locationid_from.id

        locto = [('usage', '=', 'internal'), ('active', '=', True), ('complete_name', '=', location_to)]
        locationid_to = request.env['stock.location'].sudo().search(locto)
        locto_id = locationid_to.id

        rec = request.env['product.product'].sudo().search([('barcode', '=', barcode)], limit=1)
        if not rec:
            return {"error": "Product not found"}

        product_id = rec.id
        tmpl_id = rec.product_tmpl_id.id
        rec01 = request.env['product.template'].sudo().browse(tmpl_id)
        product_uom_id = rec01.uom_id.id



    # 1. search stock.picking find id by name = 'WH/INT/00004'
        picking = request.env['stock.picking'].sudo().search([('name', '=', code)], limit=1)
        if not picking:
            return {"error": "Stock Picking not found"}
        picking_id = picking.id
    # 2. search stock.move find id by where  product_id,state,reference,picking_id,
    #  picking_type_id = 5 update state = done,quantity = ค่าจำนวนที่ต้องการโอนย้าย,location_id,location_dest_id
        move = request.env['stock.move'].sudo().search([
            ('picking_id', '=', picking_id),
            ('product_id', '=', product_id),
            ('state', '!=', 'done'),
            ('reference', '=', code),
            ('picking_type_id', '=', 5)
        ], limit=1)
        if not move:
            return {"error": "Stock Move not found"}
        upd_loc = {
            'state': 'done',
            'location_id': locfrom_id,
            'location_dest_id': locto_id,
            'quantity': transfer_qty,
        }
        move.sudo().write(upd_loc)
    # 3. search stock.move.line where move_id,picking_id,product_id
    # if found to delete
        # else loop create lot array from api
    # picking_id,move_id,company_id,product_id,product_uom_id,lot_id[array],
    # location_id,location_dest_id,product_category_name = all,state=done,
    # reference='WH/INT/00004',quantity,quantity_product_uom
    # 4 create stock_quant by loop lot
    # product_id,company_id,location_id = 23,lot_id[array],quantity,inventory_diff_quantity

        # del_line = request.env['stock.move.line'].sudo().search([
        #     ('move_id', '=', move.id),
        #     ('picking_id', '=', picking_id),
        #     ('product_id', '=', product_id),
        #
        # ], )
        # if del_line:
        #     del_line.unlink()
        query = """
        DELETE FROM stock_move_line 
        WHERE move_id = %s AND picking_id = %s AND product_id = %s
        """
        request.env.cr.execute(query, (move.id, picking_id, product_id))

        in_date = datetime.now()

        for lot_name, lot_qty in lot_no_list:
            lot = request.env['stock.lot'].sudo().search([
                ('name', '=', lot_name),
                ('product_id', '=', product_id)
            ], limit=1)

            if not lot:
                return {"error": f"Lot {lot_name} not found"}

            # หา move line เดิมก่อน
            move_line = request.env['stock.move.line'].sudo().search([
                ('move_id', '=', move.id),
                ('picking_id', '=', picking.id),
                ('product_id', '=', product_id),
                ('lot_id', '=', lot.id),
                ('state', '!=', 'done'),
            ], limit=1)

            if not move_line:
                # ถ้ายังไม่มี move line -> สร้างใหม่
                request.env['stock.move.line'].sudo().create({
                    'picking_id': picking.id,
                    'move_id': move.id,
                    'company_id': 1,
                    'product_id': product_id,
                    'product_uom_id': product_uom_id,
                    'lot_id': lot.id,
                    'location_id': locfrom_id,
                    'location_dest_id': locto_id,
                    'quantity': lot_qty,
                    'date': in_date,
                })
            else:
                # ถ้ามีแล้ว -> แก้ไข qty_done ให้ถูกต้อง
                move_line.sudo().write({
                    'qty_done': lot_qty,
                })

        # ยืนยันการย้าย (จะอัปเดต stock.quant ให้เอง)
        if picking.state not in ('done', 'cancel'):
            if picking.state == 'draft':
                picking.action_confirm()
            # ทำการ validate เพื่อให้เคลื่อนย้ายสต็อกจริง
            picking.button_validate()

        # 5. ทำการลบค่า ในstock_quant ที่ lot_id is null and product = P-02-Aurea *****************
        query = """
        DELETE FROM stock_quant
        WHERE lot_id is null AND product_id = %s
        """
        request.env.cr.execute(query, (product_id,))

        return json.dumps({'status': 'success'})

    # Transfer By Barcode
    @http.route('/set_tranfer_location_barcode', type='json', auth='public', methods=['POST'], csrf=False, website=True)
    def set_tranfer_location_barcode(self, **kw):
        # http://localhost:8069/set_tranfer_location_barcode
        # {
        #     "jsonrpc": "2.0",
        #     "params": {
        #         "code": "WH/INT/00008",
        #         "barcode": "P-01-Apollo",
        #          "location_from": "WH/สต็อก",
        #          "location_to": "WH1/Stock/WH1/LocationA",
        #         "transfer_qty": 10
        #     }
        # }

        data = http.request.params
        code = data.get('code')
        barcode = data.get('barcode')
        location_from = data.get('location_from')
        location_to = data.get('location_to')
        transfer_qty = data.get('transfer_qty')

        locfrom = [('usage', '=', 'internal'), ('active', '=', True), ('complete_name', '=', location_from)]
        locationid_from = request.env['stock.location'].sudo().search(locfrom)
        locfrom_id =  locationid_from.id

        locto = [('usage', '=', 'internal'), ('active', '=', True), ('complete_name', '=', location_to)]
        locationid_to = request.env['stock.location'].sudo().search(locto)
        locto_id = locationid_to.id


        rec = request.env['product.product'].sudo().search([('barcode', '=', barcode)], limit=1)
        if not rec:
            return {"error": "Product not found"}

        product_id = rec.id
        tmpl_id = rec.product_tmpl_id.id
        rec01 = request.env['product.template'].sudo().browse(tmpl_id)
        product_uom_id = rec01.uom_id.id



    # 1. search stock.picking find id by name = 'WH/INT/00004'
        picking = request.env['stock.picking'].sudo().search([('name', '=', code)], limit=1)
        if not picking:
            return {"error": "Stock Picking not found"}
        picking_id = picking.id
    # 2. search stock.move find id by where  product_id,state,reference,picking_id,
    #  picking_type_id = 5 update state = done,quantity = ค่าจำนวนที่ต้องการโอนย้าย,location_id,location_dest_id
        move = request.env['stock.move'].sudo().search([
            ('picking_id', '=', picking_id),
            ('product_id', '=', product_id),
            ('state', '!=', 'done'),
            ('reference', '=', code),
            ('picking_type_id', '=', 5)
        ], limit=1)
        if not move:
            return {"error": "Stock Move not found"}
        upd_loc = {
            'state': 'done',
            'quantity': transfer_qty,
        }
        move.sudo().write(upd_loc)
    # 3. search stock.move.line where move_id,picking_id,product_id
    # if found to delete
        # else loop create lot array from api
    # picking_id,move_id,company_id,product_id,product_uom_id,lot_id[array],
    # location_id,location_dest_id,product_category_name = all,state=done,
    # reference='WH/INT/00004',quantity,quantity_product_uom
    # 4 create stock_quant by loop lot
    # product_id,company_id,location_id = 23,lot_id[array],quantity,inventory_diff_quantity

        # del_line = request.env['stock.move.line'].sudo().search([
        #     ('move_id', '=', move.id),
        #     ('picking_id', '=', picking_id),
        #     ('product_id', '=', product_id),
        #
        # ], )
        # if del_line:
        #     del_line.unlink()
        query = """
        DELETE FROM stock_move_line 
        WHERE move_id = %s AND picking_id = %s AND product_id = %s
        """
        request.env.cr.execute(query, (move.id, picking_id, product_id))

        in_date = datetime.now()



        # หา move line เดิมก่อน
        move_line = request.env['stock.move.line'].sudo().search([
            ('move_id', '=', move.id),
            ('picking_id', '=', picking.id),
            ('product_id', '=', product_id),
            ('state', '!=', 'done'),
        ], limit=1)

        if not move_line:
            # ถ้ายังไม่มี move line -> สร้างใหม่
            request.env['stock.move.line'].sudo().create({
                'picking_id': picking.id,
                'move_id': move.id,
                'company_id': 1,
                'product_id': product_id,
                'product_uom_id': product_uom_id,
                'location_id': locfrom_id,
                'location_dest_id': locto_id,
                'quantity': transfer_qty,
                'date': in_date,
            })

        ## เก็บค่า quantity stock_quand เดิม
        #  location ต้นทาง Update Error

        query = """
            SELECT quantity
            FROM stock_quant
            WHERE product_id = %s AND location_id = %s
        """
        request.env.cr.execute(query, (product_id, locfrom_id))
        rows = request.env.cr.fetchall()

        from_qty = 0  # ตั้งค่า default เผื่อไม่เจอข้อมูลใน stock_quant
        for r in rows:
            from_qty = r[0]  # r เป็น tuple เช่น (10.0,)

        from_qty -= transfer_qty  # หักค่าจากจำนวนที่มีอยู่

        #
        query = """
            SELECT quantity
            FROM stock_quant
            WHERE product_id = %s AND location_id = %s
        """
        request.env.cr.execute(query, (product_id, locto_id))
        rows = request.env.cr.fetchall()

        from_qty = 0  # ตั้งค่า default เผื่อไม่เจอข้อมูลใน stock_quant
        for r in rows:
            to_qty = r[0]  # r เป็น tuple เช่น (10.0,)

        to_qty += transfer_qty  # บวกค่าจากจำนวนที่มีอยู่



        # ยืนยันการย้าย (จะอัปเดต stock.quant ให้เอง)
        if picking.state not in ('done', 'cancel'):
            if picking.state == 'draft':
                picking.action_confirm()
            # ทำการ validate เพื่อให้เคลื่อนย้ายสต็อกจริง
            picking.button_validate()

        # ทำการ update stock_quant ใหม่
        id_frm_qty = request.env['stock.quant'].sudo().search([('product_id', '=', product_id),('location_id', '=', locfrom_id)])
        frupdata_qty = {
            'quantity': from_qty,
            'reserved_quantity': from_qty,
        }
        id_frm_qty.sudo().write(frupdata_qty)

        id_to_qty = request.env['stock.quant'].sudo().search([('product_id', '=', product_id), ('location_id', '=', locto_id)])
        toupdata_qty = {
            'quantity': to_qty,
            'reserved_quantity': to_qty,
        }
        id_to_qty.sudo().write(toupdata_qty)

        return json.dumps({'status': 'success'})
####################################################################################################33
    # Transfer By Serial
    @http.route('/set_tranfer_location_sn', type='json', auth='public', methods=['POST'], csrf=False, website=True)
    def set_tranfer_location_sn(self, **kw):
        # http://localhost:8069/set_tranfer_location_sn
        # {
        #     "jsonrpc": "2.0",
        #     "params": {
        #         "code": "WH/INT/00004",
        #         "barcode": "P-03-Ember",
        #         "lot_no": [
        #             ["8801095506017"],
        #             ["8886467015144"],
        #             ["8809145603297"]
        #         ],
        #          "location_from": "WH/สต็อก",
        #          "location_to": "WH1/Stock/WH1/LocationB",
        #         "transfer_qty": 3
        #     }
        # }

        data = http.request.params
        code = data.get('code')
        barcode = data.get('barcode')
        lot_no_list = data.get('lot_no', [])  # [['lot1', qty1], ['lot2', qty2], ...]
        location_from = data.get('location_from')
        location_to = data.get('location_to')
        transfer_qty = data.get('transfer_qty')

        locfrom = [('usage', '=', 'internal'), ('active', '=', True), ('complete_name', '=', location_from)]
        locationid_from = request.env['stock.location'].sudo().search(locfrom)
        locfrom_id =  locationid_from.id

        locto = [('usage', '=', 'internal'), ('active', '=', True), ('complete_name', '=', location_to)]
        locationid_to = request.env['stock.location'].sudo().search(locto)
        locto_id = locationid_to.id

        rec = request.env['product.product'].sudo().search([('barcode', '=', barcode)], limit=1)
        if not rec:
            return {"error": "Product not found"}

        product_id = rec.id
        tmpl_id = rec.product_tmpl_id.id
        rec01 = request.env['product.template'].sudo().browse(tmpl_id)
        product_uom_id = rec01.uom_id.id



    # 1. search stock.picking find id by name = 'WH/INT/00004'
        picking = request.env['stock.picking'].sudo().search([('name', '=', code)], limit=1)
        if not picking:
            return {"error": "Stock Picking not found"}
        picking_id = picking.id
    # 2. search stock.move find id by where  product_id,state,reference,picking_id,
    #  picking_type_id = 5 update state = done,quantity = ค่าจำนวนที่ต้องการโอนย้าย,location_id,location_dest_id
        move = request.env['stock.move'].sudo().search([
            ('picking_id', '=', picking_id),
            ('product_id', '=', product_id),
            ('state', '!=', 'done'),
            ('reference', '=', code),
            ('picking_type_id', '=', 5)
        ], limit=1)
        if not move:
            return {"error": "Stock Move not found"}
        upd_loc = {
            'state': 'done',
            'location_id': locfrom_id,
            'location_dest_id': locto_id,
            'quantity': transfer_qty,
        }
        move.sudo().write(upd_loc)
    # 3. search stock.move.line where move_id,picking_id,product_id
    # if found to delete
        # else loop create lot array from api
    # picking_id,move_id,company_id,product_id,product_uom_id,lot_id[array],
    # location_id,location_dest_id,product_category_name = all,state=done,
    # reference='WH/INT/00004',quantity,quantity_product_uom
    # 4 create stock_quant by loop lot
    # product_id,company_id,location_id = 23,lot_id[array],quantity,inventory_diff_quantity

        # del_line = request.env['stock.move.line'].sudo().search([
        #     ('move_id', '=', move.id),
        #     ('picking_id', '=', picking_id),
        #     ('product_id', '=', product_id),
        #
        # ], )
        # if del_line:
        #     del_line.unlink()
        query = """
        DELETE FROM stock_move_line 
        WHERE move_id = %s AND picking_id = %s AND product_id = %s
        """
        request.env.cr.execute(query, (move.id, picking_id, product_id))

        in_date = datetime.now()

        for lot_name in lot_no_list:
            lot = request.env['stock.lot'].sudo().search([
                ('name', '=', lot_name),
                ('product_id', '=', product_id)
            ], limit=1)

            if not lot:
                return {"error": f"Lot {lot_name} not found"}

            # หา move line เดิมก่อน
            move_line = request.env['stock.move.line'].sudo().search([
                ('move_id', '=', move.id),
                ('picking_id', '=', picking.id),
                ('product_id', '=', product_id),
                ('lot_id', '=', lot.id),
                ('state', '!=', 'done'),
            ], limit=1)

            if not move_line:
                # ถ้ายังไม่มี move line -> สร้างใหม่
                request.env['stock.move.line'].sudo().create({
                    'reference': code,
                    'picking_id': picking.id,
                    'move_id': move.id,
                    'company_id': 1,
                    'product_id': product_id,
                    'product_uom_id': product_uom_id,
                    'lot_id': lot.id,
                    'location_id': locfrom_id,
                    'location_dest_id': locto_id,
                    'quantity': 1,
                    'date': in_date,
                })
            else:
                # ถ้ามีแล้ว -> แก้ไข qty_done ให้ถูกต้อง
                move_line.sudo().write({
                    'qty_done': 1,
                })

        # ยืนยันการย้าย (จะอัปเดต stock.quant ให้เอง)
        if picking.state not in ('done', 'cancel'):
            if picking.state == 'draft':
                picking.action_confirm()
            # ทำการ validate เพื่อให้เคลื่อนย้ายสต็อกจริง
            picking.button_validate()

        # 5. ทำการลบค่า ในstock_quant ที่ lot_id is null and product = P-02-Aurea *****************
        query = """
        DELETE FROM stock_quant
        WHERE lot_id is null AND product_id = %s
        """
        request.env.cr.execute(query, (product_id,))

        return json.dumps({'status': 'success'})

#######################################################################################################

    ################################ End New Stock Internal Transfer  #####

    @http.route('/stock_receive', type="json", auth='public', methods=['POST'], csrf=False, website=True)
    def stock_receive(self, **kwargs):
        data = http.request.params

        barcode = data['barcode']
        from_location = '4'
        to_location = '8'
        warranty = int(data['warranty'])
        sn = data['sn']
        po = data['po']
        state = ''

        rec02 = request.env['stock.picking'].sudo().search([('origin', '=', po)])
        picking_id = rec02.id
        pick_state = rec02.state

        rec03 = request.env['stock.move'].sudo().search([('origin', '=', po)])
        move_id = rec03.id

        rec = request.env['product.product'].sudo().search([('barcode', '=', barcode)])
        if rec:
            product_id = rec.id
            tmpl_id = rec.product_tmpl_id.id
            rec01 = request.env['product.template'].sudo().search([('id', '=', tmpl_id)])
            uom_id = rec01.uom_id.id
            # หน่วยรอง
            # rec01.update({'rt_secondary_uom': 2})

            ###  Create 1 Record in stock_lot เพื่อเก็บ SN
            if pick_state != 'done':

                # เวลาปัจจุบัน + warraty = วันหมดอายุ expiration_date
                current_date = datetime.now()
                due_date = current_date.replace(year=current_date.year + warranty)

                request.env['stock.lot'].sudo().create({
                    'product_id': product_id,
                    'product_uom_id': uom_id,
                    'name': sn,
                    'warranty': warranty,
                    # 'expiration_date': due_date,
                })




            elif pick_state == 'done':
                print('')

            rec04 = request.env['stock.lot'].sudo().search([('name', '=', sn)])
            lot_id = rec04.id

            ###  Create 1 Record in stock_quart เพื่อเก็บ SN

            fquantity = 0
            finventory_diff_quantity = 0
            tquantity = 0
            tinventory_diff_quantity = 0

            if from_location == '4':
                fquantity = -1
                finventory_diff_quantity = 1

            if to_location == '8':
                tquantity = 1
                tinventory_diff_quantity = -1

            request.env['stock.quant'].sudo().create({
                'product_id': product_id,
                'location_id': from_location,
                'lot_id': lot_id,
                'quantity': fquantity,
                'inventory_diff_quantity': finventory_diff_quantity,

            })

            request.env['stock.quant'].sudo().create({
                'product_id': product_id,
                'location_id': to_location,
                'lot_id': lot_id,
                'quantity': tquantity,
                'inventory_diff_quantity': tinventory_diff_quantity,

            })

            ## Update stock_move
            domain = [('picking_id', '=', picking_id), ('move_id', '=', move_id), ('lot_name', '=', False)]
            rec05 = request.env['stock.move.line'].sudo().search(domain, limit=1)
            if rec05:
                lot_id = lot_id
                lot_name = sn

                updata = {
                    'lot_id': lot_id,
                    'lot_name': sn,
                    'state': 'done',
                    'qty_done': 1
                }
                rec05.sudo().write(updata)

                # ทำการ Update table purchase_order_line set qty_received = จำนวน SN ที่ยิงรับเข้า อ่านค่าเก่าแล้วบวกเพิ่ม 1
                rec07 = request.env['purchase.order'].sudo().search([('name', '=', po)])
                order_id = rec07.id
                rec08 = request.env['purchase.order.line'].sudo().search(
                    [('order_id', '=', order_id), ('product_id', '=', product_id)])
                purchase_id_line = rec08.id
                product_qty = rec08.product_qty

                qty_received = rec08.qty_received + 1

                updata = {
                    'qty_received': qty_received,
                }
                rec08.sudo().write(updata)

                if qty_received != product_qty:
                    state = 'assigned'
                elif qty_received == product_qty:
                    state = 'done'

            # เมื่อ API ส่งค่า state = done มา จะต้องทำการ update state ของ stock_move,stock_picking = done ด้วย origin = PO
            if state == 'done':
                # อัปเดต stock_move ทั้งหมดที่ตรงกับ origin
                move_ids = request.env['stock.move'].sudo().search([('origin', '=', po)])
                move_ids.write({'state': 'done'})

                # อัปเดต stock_picking ที่ตรงกับ origin
                picking_ids = request.env['stock.picking'].sudo().search([('origin', '=', po)])
                picking_ids.write({'state': 'done'})
            return {'success': True, 'message': 'จำนวนสินค้าครบแล้ว'}

    @http.route('/receive_product', type="json", auth='public', methods=['POST'], csrf=False, website=True)
    def receive_product(self, **kwargs):

        ###แก้ parner_id ของ stock_move stock_picking ให้หาจากตัว customer มา แทนค่าที่ fix

        data = http.request.params

        name = data['name']
        model = data['model']
        brand = data['brand']
        sn = data['sn']
        barcode = data['barcode']
        # ram = data['ram']
        # hdd = data['hdd']
        # cpu = data['cpu']
        from_location = 4
        to_location = 8
        warranty = int(data['warranty'])
        state = ''
        current_date = datetime.now()
        due_date = current_date.replace(year=current_date.year + warranty)

        # สร้าง description โดยรวม ram, hdd และ cpu
        # สร้าง record ใน product_template

        check = request.env['product.product'].sudo().search([('barcode', '=', barcode)], limit=1)

        if not check:
            rec = request.env['product.template'].sudo().create({
                'categ_id': 1,
                'uom_id': 1,
                'uom_po_id': 1,
                'detailed_type': 'product',
                'priority': '1',
                'name': name,
                'model': model,
                'brand': brand,
                # 'ram': ram,
                # 'hdd': hdd,
                # 'cpu': cpu,
                'sale_line_warn': 'no-message',
                'invoice_policy': 'order',
                'service_tracking': 'no',
                'tracking': 'serial',
                'base_unit_count': 0,
            })

            # update record ใน product_product
            product_tem_id = rec.id
            update_p = request.env['product.product'].sudo().search([('product_tmpl_id', '=', product_tem_id)])
            update_p.write({'barcode': barcode})
            update_p.write({'default_code': 'IT'})

            rec1 = request.env['product.product'].sudo().search([('barcode', '=', barcode)])
            product_id = rec1.id

            # สร้าง record ใน stock_picking
            pick_id = request.env['stock.picking'].sudo().create({
                'location_id': from_location,
                'location_dest_id': to_location,
                'picking_type_id': 1,
                'company_id': 1,
                'origin': 'PO',
                'move_type': 'direct',
                'state': 'assigned',
                'scheduled_date': current_date,
            })

            # สร้าง record ใน stock_move
            move_id = request.env['stock.move'].sudo().create({
                'company_id': 1,
                'product_id': product_id,
                'product_uom': 1,
                'location_id': from_location,
                'location_dest_id': to_location,
                'name': name,
                'partner_id': 25,  # สร้างตัว search ไปหาค่ามา ไม่ควร fix ค่า
                'picking_id': pick_id.id,
                'origin': 'PO',
                'state': 'assigned',
                'picking_type_id': 1,
                'procure_method': 'make_to_stock',
                'product_uom_qty': 1,
                'quantity_done': 0,
                'date': current_date,
            })
            # stock_ lot สร้าง record
            lot_id = request.env['stock.lot'].sudo().create({
                'product_id': product_id,
                'product_uom_id': 1,
                'company_id': 1,
                'name': sn,
                'warranty': warranty,
                # 'expiration_date': due_date,
            })
            # stock_move_line สร้าง record
            request.env['stock.move.line'].sudo().create({
                'picking_id': pick_id.id,
                'move_id': move_id.id,
                'company_id': 1,
                'product_id': product_id,
                'product_uom_id': 1,
                'location_id': from_location,
                'location_dest_id': to_location,
                'lot_id': lot_id.id,
                'lot_name': sn,
                'state': 'done',
                'reserved_uom_qty': 1,
                'qty_done': 1,
                'date': current_date,
            })
            # ทำ state stock_picking and stock_move = done

            picking_ids = request.env['stock.picking'].sudo().search([('id', '=', pick_id.id)])
            picking_ids.write({'state': 'done'})

            move_ids = request.env['stock.move'].sudo().search([('id', '=', move_id.id)])
            move_ids.write({'state': 'done'})

            ###สร้าง stock_quant ตอนรับสินค้าเสร็จสิ้น
            ###  Create 1 Record in stock_quart เพื่อเก็บ SN

            ###  Create 1 Record in stock_quart เพื่อเก็บ SN
            if move_ids.state == 'done':
                fquantity = 0
                finventory_diff_quantity = 0
                tquantity = 0
                tinventory_diff_quantity = 0

                if from_location == 4:
                    fquantity = -1
                    finventory_diff_quantity = 1

                if to_location == 8:
                    tquantity = 1
                    tinventory_diff_quantity = -1

                request.env['stock.quant'].sudo().create({
                    'product_id': product_id,
                    'location_id': from_location,
                    'lot_id': lot_id.id,
                    'quantity': fquantity,
                    'inventory_diff_quantity': finventory_diff_quantity,

                })

                request.env['stock.quant'].sudo().create({
                    'product_id': product_id,
                    'location_id': to_location,
                    'lot_id': lot_id.id,
                    'quantity': tquantity,
                    'inventory_diff_quantity': tinventory_diff_quantity,

                })

            return {'success': True, }




        else:
            rec1 = request.env['product.product'].sudo().search([('barcode', '=', barcode)])
            product_id = rec1.id

            # สร้าง record ใน stock_picking
            pick_id = request.env['stock.picking'].sudo().create({
                'location_id': from_location,
                'location_dest_id': to_location,
                'partner_id': 25,
                'picking_type_id': 1,
                'company_id': 1,
                'origin': 'PO',
                'move_type': 'direct',
                'state': 'assigned',
                'scheduled_date': current_date,
            })

            # สร้าง record ใน stock_move
            move_id = request.env['stock.move'].sudo().create({
                'company_id': 1,
                'product_id': product_id,
                'product_uom': 1,
                'location_id': from_location,
                'location_dest_id': to_location,
                'name': name,
                'partner_id': 25,
                'picking_id': pick_id.id,
                'origin': 'PO',
                'state': 'assigned',
                'picking_type_id': 1,
                'procure_method': 'make_to_stock',
                'product_uom_qty': 1,
                'quantity_done': 0,
                'date': current_date,
            })
            # stock_ lot สร้าง record
            lot_id = request.env['stock.lot'].sudo().create({
                'product_id': product_id,
                'product_uom_id': 1,
                'company_id': 1,
                'name': sn,
                'warranty': warranty,
                # 'expiration_date': due_date,
            })

            # stock_move_line สร้าง record
            request.env['stock.move.line'].sudo().create({
                'picking_id': pick_id.id,
                'move_id': move_id.id,
                'company_id': 1,
                'product_id': product_id,
                'product_uom_id': 1,
                'location_id': from_location,
                'location_dest_id': to_location,
                'lot_name': sn,
                'lot_id': lot_id.id,
                'state': 'done',
                'reference': 'REV',
                'reserved_uom_qty': 1,
                'qty_done': 1,
                'date': current_date,
            })
            # ทำ state stock_picking and stock_move = done

            picking_ids = request.env['stock.picking'].sudo().search([('id', '=', pick_id.id)])
            picking_ids.write({'state': 'done'})

            move_ids = request.env['stock.move'].sudo().search([('id', '=', move_id.id)])
            move_ids.write({'state': 'done'})

            ###  Create 1 Record in stock_quart เพื่อเก็บ SN
            if move_ids.state == 'done':
                fquantity = 0
                finventory_diff_quantity = 0
                tquantity = 0
                tinventory_diff_quantity = 0

                if from_location == 4:
                    fquantity = -1
                    finventory_diff_quantity = 1

                if to_location == 8:
                    tquantity = 1
                    tinventory_diff_quantity = -1

                request.env['stock.quant'].sudo().create({
                    'product_id': product_id,
                    'location_id': from_location,
                    'lot_id': lot_id.id,
                    'quantity': fquantity,
                    'inventory_diff_quantity': finventory_diff_quantity,

                })

                request.env['stock.quant'].sudo().create({
                    'product_id': product_id,
                    'location_id': to_location,
                    'lot_id': lot_id.id,
                    'quantity': tquantity,
                    'inventory_diff_quantity': tinventory_diff_quantity,

                })
            return {'success': True, }


    ################################  Stock Issue  ###########################################

    @http.route('/api/get_so_number', type="json", auth='public', methods=['POST'])
    def get_so_number(self):
        try:
            # ค้นหาประเภทการ picking ที่มี sequence_code เป็น 'in'
            picking_types = request.env['stock.picking.type'].sudo().search([
                ('sequence_code', '=', 'OUT')
            ])

            # ดึง IDs ของ picking types ที่ตรงกับเงื่อนไข
            picking_type_ids = picking_types.mapped('id')

            # ค้นหาข้อมูล stock.picking ที่มีสถานะเป็น 'assigned', origin ไม่ว่าง, และ picking_type ตรงกับที่ค้นหา
            locations = request.env['stock.picking'].sudo().search([
                ('state', '=', 'confirmed'),
                ('origin', '!=', False),  # ตรวจสอบว่า origin ไม่เป็น False หรือว่าง
                ('picking_type_id', 'in', picking_type_ids)  # ตรวจสอบว่า picking_type ตรงกับที่ค้นหา
            ])

            # คืนค่าข้อมูลในรูปแบบที่ต้องการ
            return [{'id': loc.id, 'name': loc.origin} for loc in locations]
        except Exception as e:
            # การจัดการข้อผิดพลาด
            return {'error': str(e)}




    ##### issue by product

    @http.route('/stock_issue', type="json", auth='public', methods=['POST'], csrf=False, website=True)
    def stock_issue(self, **kwargs):
        data = http.request.params

        barcode = data['barcode']
        from_location = '8'
        to_location = '5'
        sn = data['sn']
        so = data['so']
        state = ''

        rec = request.env['product.product'].sudo().search([('barcode', '=', barcode)])
        if rec:
            product_id = rec.id
            tmpl_id = rec.product_tmpl_id.id
            rec01 = request.env['product.template'].sudo().search([('id', '=', tmpl_id)])
            uom_id = rec01.uom_id.id

            rec04 = request.env['stock.lot'].sudo().search([('name', '=', sn)])
            lot_id = rec04.id
            lot_name = rec04.name

            # insert stock_move_line มีฟิล insert = piking_id ,move_id, company_id = 1, product_id , product_uom_id
            # location_id ,location_dest_id ,state = done , lot_id , lot_name , reference , reserved_qty = 1 ,
            # reserved_uom_qty  = 1 ,qty_done = 0
            rec02 = request.env['stock.picking'].sudo().search([('origin', '=', so)])
            picking_id = rec02.id

            rec03 = request.env['stock.move'].sudo().search([('origin', '=', so)])
            move_id = rec03.id
            reference = rec03.reference

            request.env['stock.move.line'].sudo().create({
                'picking_id': picking_id,
                'move_id': move_id,
                'company_id': 1,
                'product_id': product_id,
                'product_uom_id': uom_id,
                'location_id': from_location,
                'location_dest_id': to_location,
                'state': 'done',
                'lot_id': lot_id,
                'lot_name': lot_name,
                'reference': reference,
                'reserved_uom_qty': 1,
                'qty_done': 1
            })

            # แก้ไข location จาก 8 เป็น 5 stock_quant 1 record เมื่อทำการยิง และลบรายการที่ odoo gen lot มาให้เอาออก
            rec06 = request.env['stock.quant'].sudo().search([('lot_id', '=', lot_id), ('location_id', '=', 8)])
            rec06.write({'location_id': 5})

            # บวกเพิ่ม 1 ใน sale_order_line บนฟิลด์ qty_delivered
            rec05 = request.env['sale.order'].sudo().search([('name', '=', so)])
            order_id = rec05.id
            rec06 = request.env['sale.order.line'].sudo().search(
                [('order_id', '=', order_id), ('product_id', '=', product_id)])
            sale_id_line = rec06.id
            qty_to_invoice = rec06.qty_to_invoice
            qty_delivered = rec06.qty_delivered + 1

            updata = {
                'qty_delivered': qty_delivered,
            }
            rec06.sudo().write(updata)

            # เช็คจำนวนสิ้นค้าขาออก ถ้าจำนวนสินค้าออกยังไม่ครบ state = assigned ถ้าครบ state = done

            if qty_delivered != qty_to_invoice:
                state = 'assigned'
            elif qty_delivered == qty_to_invoice:
                state = 'done'

            # return {'success': True, 'message': 'จำนวนสินค้าครบแล้ว'}
            # ถ้าเกิดส่งค่า state = done มาแล้ว ต้องไปอัพเดตใน stock_move , stock_picking ให้ state = done
            if state == 'done':
                # อัปเดต stock_move ทั้งหมดที่ตรงกับ origin
                move_ids = request.env['stock.move'].sudo().search([('origin', '=', so)])
                move_ids.write({'state': 'done'})

                # อัปเดต stock_picking ที่ตรงกับ origin
                picking_ids = request.env['stock.picking'].sudo().search([('origin', '=', so)])
                picking_ids.write({'state': 'done'})
            return {'success': True, 'message': 'จำนวนสินค้าครบแล้ว'}

    ################################  Stock Transfer  ###########################################
    @http.route('/api/from_location', type="json", auth='public', methods=['POST'])
    def from_location(self):
        try:

            # ค้นหาข้อมูล stock.picking ที่มีสถานะเป็น 'assigned', origin ไม่ว่าง, และ picking_type ตรงกับที่ค้นหา
            locations = request.env['stock.location'].sudo().search([('usage', '=', 'internal')

                                                                     ])

            # คืนค่าข้อมูลในรูปแบบที่ต้องการ
            return [{'id': loc.id, 'name': loc.complete_name} for loc in locations]
        except Exception as e:
            # การจัดการข้อผิดพลาด
            return {'error': str(e)}

    @http.route('/stock_transfer', type="json", auth='public', methods=['POST'], csrf=False, website=True)
    def stock_transfer(self, **kwargs):
        data = http.request.params
        owner = data['owner']
        department = data['department']
        barcode = data['barcode']
        from_location = data['from_location']
        product_uom_qty = data['product_uom_qty']
        to_location = data['to_location']
        sn = data['sn']
        state = ''
        name_picking = data['name_picking']
        # ส่งค่า product_qty , ถ้ายิงครั้งแรกให้ส่งค่า flag = T ครั้งต่อไปให้ส่ง flag = F
        flag = data['flag']

        rec = request.env['product.product'].sudo().search([('barcode', '=', barcode)])
        if rec:
            product_id = rec.id
            tmpl_id = rec.product_tmpl_id.id
            rec01 = request.env['product.template'].sudo().search([('id', '=', tmpl_id)])
            uom_id = rec01.uom_id.id
            name = rec01.name
        if flag == 't':
            pick_id = request.env['stock.picking'].sudo().create({
                'picking_type_id': 5,
                'location_id': from_location,
                'location_dest_id': to_location,
                'state': 'assigned'
            })

            move_id = request.env['stock.move'].sudo().create({
                'company_id': 1,
                'product_id': product_id,
                'product_uom': uom_id,
                'picking_id': pick_id.id,
                'location_id': from_location,
                'location_dest_id': to_location,
                'picking_type_id': 5,
                'name': name,
                'procure_method': 'make_to_stock',
                'product_uom_qty': product_uom_qty,
                'state': 'assigned',
            })
            return {'success': True, 'message': 'จำนวนสินค้าครบแล้ว', 'name_picking': pick_id.name}
        if flag == 'f':
            rec04 = request.env['stock.lot'].sudo().search([('name', '=', sn)])
            lot_id = rec04.id
            lot_name = rec04.name

            updata = {
                'owner': owner,
                'department': department,
            }
            rec04.sudo().write(updata)

            from_location = int(from_location)
            to_location = int(to_location)

            rec07 = request.env['stock.picking'].sudo().search([('name', '=', name_picking)])
            picking_id = rec07.id

            rec08 = request.env['stock.move'].sudo().search([('picking_id', '=', picking_id)])
            move_id1 = rec08.id
            reference = rec08.reference

            # create 1 record ใน stock.move.line
            request.env['stock.move.line'].sudo().create({
                'picking_id': picking_id,
                'move_id': move_id1,
                'company_id': 1,
                'product_id': product_id,
                'product_uom_id': uom_id,
                'location_id': from_location,
                'location_dest_id': to_location,
                'state': 'done',
                'lot_id': lot_id,
                'lot_name': lot_name,
                'reference': reference,
                'reserved_uom_qty': 1,
                'qty_done': 1
            })

            # เช็คค่าใน stock_move ถ้า product_uom_qty และ quatity_done เท่ากันเมื่อไหร่ให้ state stock_picking  = done , stock_move = done
            rec09 = request.env['stock.move'].sudo().search([('picking_id', '=', picking_id)])
            id_move = rec09.id
            picking_id1 = rec09.picking_id.id
            product_uom_qty = rec09.product_uom_qty
            quantity_done = rec09.quantity_done

            if product_uom_qty == quantity_done:
                picking_ids = request.env['stock.picking'].sudo().search([('id', '=', picking_id1)])
                picking_ids.write({'state': 'done'})

                move_ids = request.env['stock.move'].sudo().search([('id', '=', id_move)])
                move_ids.write({'state': 'done'})
            ###อัพเดต stock_quant ตอนย้ายสินค้าเสร็จสิ้น
            update_stock = request.env['stock.quant'].sudo().search(
                [('lot_id', '=', lot_id), ('location_id', '=', from_location)])
            update_stock.write({'location_id': to_location})
            return {'success': True, 'message': 'จำนวนสินค้าครบแล้ว'}


    ################################  Stock Count  ###########################################
    @http.route('/stock_counting', type="json", auth='public', methods=['POST'], csrf=False)
    def counting_stock(self):
        data = http.request.params

        sn = data['sn']
        name = data['name']

        # หา prod_lot_id ใน stock.inventory.line หาจาก id ของ stock_lot
        # rec1 = request.env['stock.inventory'].sudo().search([('name', '=', name)])
        # rec2 = request.env['stock.inventory.line'].sudo().search(
        #     [('inventory_id', '=', rec1.id), ('location_id', '=', rec1.locationis.id)], limit=1)
        # rec3 = request.env['stock.inventory.line'].sudo().search(
        #     [('inventory_id', '=', rec1.id), ('location_id', '=', rec1.locationis.id)])

        # if rec2.checkid == 'f':
        #     rec3.write({'qty_done': 0})
        #     rec3.write({'checkid': 't'})

        # if sn != None:
        #     rec = request.env['stock.inventory.line'].sudo().search([('prod_lot_id', '=', sn)])
        #     rec.write({'qty_done': 1})
        #     return {'success': True}


    @http.route('/sale_lot', type="json", auth='public', methods=['POST'], csrf=False)
    def sale_lot(self):
        # Search for all sale orders
        rec = request.env['sale.order'].sudo().search([])

        # Create a list to store the sale order information
        so_numbers = []

        # Populate the list with sale order information
        for order in rec:
            so_numbers.append({
                'name': order.name,
                'date_order': order.date_order,
                'amount_total': order.amount_total,
                # Add any other fields you need here
            })

        return {
            'jsonrpc': '2.0',
            'result': so_numbers,
        }



    ################################  Stock Master check  ###########################################
    @http.route('/check_warranty', type="json", auth='public', methods=['POST'], csrf=False)
    def check_warranty(self):
        data = http.request.params
        sn = data['sn']

        # ส่งค่าวันหมดอายุ get_warranty
        get_rec = request.env['stock.lot'].sudo().search([('name', '=', sn)])
        rec_owner = request.env['hr.employee'].sudo().search([('id', '=', get_rec.owner.id)])
        rec_department = request.env['hr.department'].sudo().search([('id', '=', get_rec.department.id)])
        name_owner = rec_owner.name
        name_department = rec_department.name
        # expiration_date = get01.expiration_date.strftime('%Y-%m-%d %H:%M:%S')
        # warranty = get01.warranty

        if get_rec:
            return {
                'id': get_rec.id,
                # 'expiration_date': get_rec.expiration_date,
                'warranty': get_rec.warranty,
                'department': name_department,
                'owner': name_owner,
                'message': 'found',
            }
        else:
            return {
                'id': 'NO',
                'warranty': 'NO',
                # 'expiration_date': 'NO',
                'department': 'NO',
                'owner': 'NO',
                'message': 'No stock quant record found.',
            }

    @http.route('/check_lot', type="json", auth='public', methods=['POST'], csrf=False)
    def check_lot(self):
        data = http.request.params
        po = data['po']
        barcode = data['barcode']

        # ส่งค่าวันหมดอายุ get_warranty
        # get_rec = request.env['stock.lot'].sudo().search([('name', '=', po)])
        # rec_owner = request.env['hr.employee'].sudo().search([('id', '=', get_rec.owner.id)])
        # rec_department = request.env['hr.department'].sudo().search([('id', '=', get_rec.department.id)])
        # name_owner = rec_owner.name
        # name_department = rec_department.name
        # expiration_date = get01.expiration_date.strftime('%Y-%m-%d %H:%M:%S')
        # warranty = get01.warranty
        get_rec = request.env['stock.picking'].sudo().search([('origin', '=', po)])
        move_id = request.env['stock.move'].sudo().search([('picking_id', '=', get_rec.id)])

        if move_id:
            return {
                'qty': move_id.product_uom_qty
            }
        else:
            return {
                'id': 'NO',
                'warranty': 'NO',
                # 'expiration_date': 'NO',
                'department': 'NO',
                'owner': 'NO',
                'message': 'No stock quant record found.',
            }

    @http.route('/get_owner', type="json", auth='public', methods=['POST'], csrf=False)
    def get_owner(self):
        try:

            # หา owner
            employees = request.env['hr.employee'].sudo().search([])

            return [{'id': loc.id, 'name': loc.name} for loc in employees]

        except Exception as e:
            # การจัดการข้อผิดพลาด
            return {'error': str(e)}

    @http.route('/get_department', type="json", auth='public', methods=['POST'], csrf=False)
    def get_department(self):
        try:
            # หา owner
            departments = request.env['hr.department'].sudo().search([])
            return [{'id': loc.id, 'name': loc.name} for loc in departments]
        except Exception as e:
            # การจัดการข้อผิดพลาด
            return {'error': str(e)}
        # หา department
        departments = request.env['hr.department'].sudo().search([])

    # @http.route('/get_inventory', type="json", auth='public', methods=['POST'], csrf=False)
    # def get_inventory(self):
    #     try:
    #         # หา name stock.inventory
    #         inventory = request.env['stock.inventory'].sudo().search([('state', '=', 'confirm')])
    #         return [{'id': name.id, 'name': name.name} for name in inventory]
    #     except Exception as e:
    #         # การจัดการข้อผิดพลาด
    #         return {'error': str(e)}





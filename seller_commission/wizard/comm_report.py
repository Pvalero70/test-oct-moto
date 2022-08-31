# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import AccessError, UserError, ValidationError
import logging
import io
import base64
import datetime
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
DATE_FORMAT = "%Y-%m-%d"
_log = logging.getLogger("__--__-->> Report Commission:: ")

NUM_MONTHS = {
    "1": 'Enero',
    "2": "Febrero",
    "3": "Marzo",
    "4": "Abril",
    "5": "Mayo",
    "6": "Junio",
    "7": "Julio",
    "8": "Agosto",
    "9": "Septiembre",
    "10": "Octubre",
    "11": "Noviembre",
    "12": "Diciembre"
}


class CommWizardReport(models.TransientModel):
    _name = "comm.wizard.report"
    _description = "Wizard que genera reportes de EXCEL de comisiones de vendedores o mecánicos."

    month_start = fields.Selection([
        ("1", 'Enero'),
        ("2", "Febrero"),
        ("3", "Marzo"),
        ("4", "Abril"),
        ("5", "Mayo"),
        ("6", "Junio"),
        ("7", "Julio"),
        ("8", "Agosto"),
        ("9", "Septiembre"),
        ("10", "Octubre"),
        ("11", "Noviembre"),
        ("12", "Diciembre")
    ], string="Mes", required=True)
    month_final = fields.Selection([
        ("1", 'Enero'),
        ("2", "Febrero"),
        ("3", "Marzo"),
        ("4", "Abril"),
        ("5", "Mayo"),
        ("6", "Junio"),
        ("7", "Julio"),
        ("8", "Agosto"),
        ("9", "Septiembre"),
        ("10", "Octubre"),
        ("11", "Noviembre"),
        ("12", "Diciembre")
    ], string="Mes", required=False,
        help="Si no se indica se sobre entiende que el reporte es por el primer mes.")
    year = fields.Selection([
        ("2021", "2021"),
        ("2022", "2022"),
        ("2023", "2023"),
        ("2024", "2024")
    ], string="Año", required=False,
        help="Se puede indicar el año, de lo contrario se considera el actual")
    ambit = fields.Selection([
        ('refacc', 'Refacciones y accesorios'),
        ('motos', 'Motocicletas'),
        ('servicios', 'Servicios')
    ], required=True, help="Reporte")
    include_paid_comms = fields.Boolean(string="Incluye comisiones pagadas")

    excel_file = fields.Binary('excel file')
    file_name = fields.Char('Nombre del Archivo', size=128)

    def get_report(self):
        if self.ambit == "servicios":
            return self.mechanic_report()
        elif self.ambit == "motos":
            return self.motos_report()
        elif self.ambit == "refacc":
            return self.ref_acc_report()
        else:
            return False

    def mechanic_report(self):
        # Si no especifican un año, se considera el actual.
        if self.year:
            current_year = int(self.year)
        else:
            current_year = fields.Date().today().year
        _log.info("AÑO considerado :: %s " % current_year)


        # Considerar que seleccionen el mismo mes o bien que seleccionen el primero o bien uno de los dos.
        if self.month_final:
            self.file_name = 'Servicios %s a %s de %s.xlsx' % (NUM_MONTHS[self.month_start], NUM_MONTHS[self.month_final], current_year)
            fp = io.BytesIO()
            months = self.create_month_range(self.month_start, self.month_final)
            domain = [
                ('current_month', 'in', months)
            ]
        else:
            self.file_name = 'Servicios del %s-%s.xlsx' % (NUM_MONTHS[self.month_start], current_year)
            fp = io.BytesIO()
            domain = [
                ('current_month', '=', self.month_start)
            ]

        if not self.include_paid_comms:
            domain.append(('state', '=', "to_pay"))
        comm_ids_unfiltered = self.env['seller.commission'].search(domain)
        # _log.info("AÑOS EN LAS COMISIONES ::: %s - > %s " % (comm_ids_unfiltered.mapped("create_date"), comm_ids_unfiltered.mapped("create_date").year))
        # Si existe el filtro por año; considerarlo:
        comm_ids = comm_ids_unfiltered.filtered(lambda cy: current_year == cy.create_date.year)
        if not comm_ids:
            raise UserError("No se encontraron comisiones con los datos especificados.")
        mechanic_ids = comm_ids.mapped('mechanic_id')
        workbook = xlsxwriter.Workbook(fp, {'in_memory': True})
        title = workbook.add_format(
            {'bold': True,
             'font_size': 18,
             'bg_color': 'white',
             'center_across': True
             })
        encabezados = workbook.add_format(
            {'bold': True,
             'font_size': 10,
             'bg_color': '#B7F9B0',
             'center_across': True
             })
        datas = workbook.add_format(
            {'bold': False,
             'font_size': 10,
             'bg_color': 'white',
             'center_across': True
             })
        datas2 = workbook.add_format(
            {'bold': False,
             'font_size': 10,
             'bg_color': 'yellow',
             'center_across': True
             })
        _log.info(" MECANICOS .... :: :%s " % mechanic_ids)
        all_mechanic_totals = []
        for mechanic in mechanic_ids:
            sheet = workbook.add_worksheet('%s' % mechanic.display_name)
            vertical_offset_table = 3
            sheet.set_column(0, 5, 20)
            sheet.set_column(6, 6, 30)
            sheet.set_column(7, 12, 20)

            sheet.merge_range(1, 5, 1, 8, self.env.company.name, title)
            sheet.write(1, 1, fields.Date().today().strftime(DATE_FORMAT))

            sheet.write(vertical_offset_table, 0, 'Orden reparación', encabezados)
            sheet.write(vertical_offset_table, 1, 'Fecha orden', encabezados)
            sheet.write(vertical_offset_table, 2, 'Factura', encabezados)
            sheet.write(vertical_offset_table, 3, 'Fecha factura', encabezados)
            sheet.write(vertical_offset_table, 4, 'Venta tpv', encabezados)
            sheet.write(vertical_offset_table, 5, 'Modelo', encabezados)
            sheet.write(vertical_offset_table, 6, 'Servicio', encabezados)
            sheet.write(vertical_offset_table, 7, 'Cantidad', encabezados)
            sheet.write(vertical_offset_table, 8, 'P. Unitario', encabezados)
            sheet.write(vertical_offset_table, 9, 'Subtotal', encabezados)
            sheet.write(vertical_offset_table, 10, 'Regla comisión', encabezados)
            sheet.write(vertical_offset_table, 11, 'Comisión', encabezados)

            # Comisiones de mecánico.
            mechanic_coms = comm_ids.filtered(lambda co: co.mechanic_id and co.mechanic_id.id == mechanic.id)
            mc_prelines_applied = mechanic_coms.mapped('preline_ids').filtered(lambda pl: pl.commission_line_id is not False)
            row_pl = 1
            # Buscar las lineas relacionadas (rec_id) y en el ciclo abajo
            # las filtramos.

            # Sumatorias.
            clamount_total = 0
            qty_services_total = 0
            sum_comms_factor = 0

            _log.info("PRELINAS:: %s " % mc_prelines_applied)
            last_table_row = 0
            for mcpl in mc_prelines_applied:
                rol = self.env['repair.fee'].browse(mcpl.rec_id)
                # Calculo de la linea con la regla exacta. 
                if mcpl.commission_line_id.comm_rule.calc_method == "fixed":
                    clamount = rol.product_uom_qty * mcpl.commission_line_id.comm_rule.amount_factor
                else:
                    factor = mcpl.commission_line_id.comm_rule.amount_factor/100
                    clamount = mcpl.amount*factor

                # Tabla
                current_row = row_pl + vertical_offset_table
                sheet.write(current_row, 0, rol.repair_id.name, datas)
                sheet.write(current_row, 1, rol.repair_id.create_date.strftime(DATE_FORMAT), datas)
                # sheet.write(current_row, 1, rol.repair_id.create_date.strftime("%Y-%m-%dT%H:%M:%S"))
                sheet.write(current_row, 2, mcpl.invoice_id.state, datas)
                sheet.write(current_row, 3, mcpl.invoice_id.invoice_date.strftime(DATE_FORMAT), datas)
                sheet.write(current_row, 4, rol.repair_id.tpv_ids[0].name, datas)
                sheet.write(current_row, 5, rol.repair_id.product_id.name, datas)
                sheet.write(current_row, 6, rol.name, datas)
                sheet.write(current_row, 7, rol.product_uom_qty, datas)
                sheet.write(current_row, 8, rol.price_unit, datas)
                sheet.write(current_row, 9, mcpl.amount, datas) # Subtotal
                sheet.write(current_row, 10, mcpl.commission_line_id.comm_rule.name, datas) # Regla de comision
                sheet.write(current_row, 11, clamount, datas)
                row_pl += 1
                last_table_row = current_row

                # Sumatorias
                qty_services_total += rol.product_uom_qty
                sum_comms_factor += mcpl.commission_line_id.comm_rule.amount_factor
                clamount_total += clamount

            totals_dic = {
                'name': mechanic.display_name,
                'service_qty': qty_services_total,
                'amount_total': clamount_total
            }
            all_mechanic_totals.append(totals_dic)

            _log.info("Suma comision total::: %s " % clamount_total)
            last_table_row += 2
            sheet.write(last_table_row, 6, 'TOTALES', encabezados)
            sheet.write(last_table_row, 7, qty_services_total, datas2)
            sheet.write(last_table_row, 10, sum_comms_factor, datas2)
            sheet.write(last_table_row, 11, clamount_total, datas2)

        sheet_totals = workbook.add_worksheet("TOTALES")
        total_voffset = 0
        count = 1
        sheet_totals.set_column(0, 0, 5)
        sheet_totals.set_column(1, 1, 25)
        sheet_totals.set_column(2, 3, 15)

        sheet_totals.write(total_voffset, 1, 'Colaborador', encabezados)
        sheet_totals.write(total_voffset, 2, 'Horas', encabezados)
        sheet_totals.write(total_voffset, 3, 'Total a percibir', encabezados)
        g_total_hours = 0
        g_total_amount = 0

        for mt in all_mechanic_totals:
            total_voffset += 1
            sheet_totals.write(total_voffset, 0, count, datas2)
            sheet_totals.write(total_voffset, 1, mt['name'], datas)
            sheet_totals.write(total_voffset, 2, mt['service_qty'], datas)
            sheet_totals.write(total_voffset, 3, mt['amount_total'], datas)
            count += 1
            g_total_amount += mt['amount_total']
            g_total_hours += mt['service_qty']
        sheet_totals.write(total_voffset+1, 2, g_total_hours, datas)
        sheet_totals.write(total_voffset+1, 3, g_total_amount, datas)

        workbook.close()
        fp.seek(0)
        self.excel_file = base64.encodestring(fp.getvalue())
        fp.close()
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        file_url = url + "/web/binary/download_document?model=comm.wizard.report&id=%s&field=excel_file&filename=%s" % (
            self.id, self.file_name)
        _log.info(file_url)
        return {
            'type': 'ir.actions.act_url',
            'url': file_url,
        }

    def motos_report(self):
        _log.info(" GENERANDO REPORTE DE MOTOS.. ")
        if self.year:
            current_year = int(self.year)
        else:
            current_year = fields.Date().today().year
        _log.info("AÑO considerado :: %s " % current_year)

        if self.month_final:
            self.file_name = 'Ventas %s a %s de %s.xlsx' % (NUM_MONTHS[self.month_start], NUM_MONTHS[self.month_final], current_year)
            fp = io.BytesIO()
            months = self.create_month_range(self.month_start, self.month_final)
            domain = [
                ('current_month', 'in', months)
            ]
        else:
            self.file_name = 'Ventas %s-%s.xlsx' % (NUM_MONTHS[self.month_start], current_year)
            fp = io.BytesIO()
            domain = [
                ('current_month', '=', self.month_start)
            ]

        if not self.include_paid_comms:
            domain.append(('state', '=', "to_pay"))
        comm_ids_unfiltered = self.env['seller.commission'].search(domain)
        comm_ids = comm_ids_unfiltered.filtered(lambda cy: current_year == cy.create_date.year and cy.seller_id is not False)
        if not comm_ids:
            raise UserError("No se encontraron comisiones con los datos especificados.")
        # Mapeamos los colaboradores que tienen pendientes comisiones desde el módulo de ventas.
        seller_ids = comm_ids.mapped('seller_id')

        # Formación del reporte.
        workbook = xlsxwriter.Workbook(fp, {'in_memory': True})
        title = workbook.add_format(
            {'bold': True,
             'font_size': 18,
             'bg_color': 'white',
             'center_across': True
             })
        encabezados = workbook.add_format(
            {'bold': True,
             'font_size': 10,
             'bg_color': '#B7F9B0',
             'center_across': True
             })
        datas = workbook.add_format(
            {'bold': False,
             'font_size': 8,
             'bg_color': 'white',
             'center_across': True
             })
        datas2 = workbook.add_format(
            {'bold': False,
             'font_size': 8,
             'bg_color': 'yellow',
             'center_across': True
             })

        for seller in seller_ids:
            sheet = workbook.add_worksheet('%s' % seller.display_name)
            vertical_offset_table = 3
            sheet.set_column(0, 1, 10)
            sheet.set_column(2, 2, 5)
            sheet.set_column(3, 3, 25)
            sheet.set_column(4, 5, 8)
            sheet.set_column(6, 6, 25)

            sheet.merge_range(1, 3, 2, 8, self.env.company.name, title)
            sheet.write(1, 1, fields.Date().today().strftime(DATE_FORMAT))

            sheet.write(vertical_offset_table, 0, 'Factura', encabezados)
            sheet.write(vertical_offset_table, 1, 'F Fecha', encabezados)
            sheet.write(vertical_offset_table, 2, '-', encabezados)
            sheet.write(vertical_offset_table, 3, 'CLiente', encabezados)
            sheet.write(vertical_offset_table, 4, 'Modelo', encabezados)
            sheet.write(vertical_offset_table, 5, 'No. Inventario', encabezados)
            sheet.write(vertical_offset_table, 6, 'Serie', encabezados)
            sheet.write(vertical_offset_table, 7, 'P. venta', encabezados)
            sheet.write(vertical_offset_table, 8, 'Costo', encabezados)
            sheet.write(vertical_offset_table, 9, 'Utilidad', encabezados)
            sheet.write(vertical_offset_table, 10, 'Comisión', encabezados)

            # Filtro de las comisiones del vendedor y obtención de sus prelineas, las cuales no deben ser ventas hechas desde una reparación.
            seller_coms = comm_ids.filtered(lambda co: co.seller_id and co.seller_id.id == seller.id)
            seller_prelines_applied = seller_coms.mapped('preline_ids').filtered(lambda pl: pl.commission_line_id is not False and not pl.is_repair_sale)

            # Acumuladores
            row_pl = 1
            seller_commission_total = 0
            # Iteración de las prelineas.
            for spa in seller_prelines_applied:
                order_line = self.env['sale.order.line'].browse(spa.rec_id)
                if not order_line:
                    continue

                # Calcular comisión de prelinea.
                if spa.commission_line_id.comm_rule.calc_method == "fixed":
                    clamount = order_line.product_uom_qty * spa.commission_line_id.comm_rule.amount_factor
                else:
                    factor = spa.commission_line_id.comm_rule.amount_factor/100
                    clamount = spa.amount*factor

                # Tabla
                current_row = row_pl + vertical_offset_table
                sheet.write(current_row, 0, spa.invoice_id.name, datas)
                sheet.write(current_row, 1, spa.invoice_id.invoice_date.strftime(DATE_FORMAT), datas)
                sheet.write(current_row, 2, " ", datas)
                sheet.write(current_row, 3, order_line.order_id.partner_id.name, datas)
                sheet.write(current_row, 4, order_line.product_id.moto_model, datas)
                sheet.write(current_row, 5, order_line.lot_id.tt_inventory_number, datas)
                sheet.write(current_row, 6, order_line.lot_id.name, datas)
                sheet.write(current_row, 7, order_line.price_subtotal, datas)
                sheet.write(current_row, 8, order_line.purchase_price, datas)
                sheet.write(current_row, 9, order_line.margin, datas)
                sheet.write(current_row, 9, order_line.margin, datas)
                sheet.write(current_row, 10, clamount, datas)
                row_pl += 1
                seller_commission_total += clamount


        # Finalizado el reporte se construye el binario.
        workbook.close()
        fp.seek(0)
        self.excel_file = base64.encodestring(fp.getvalue())
        fp.close()
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        file_url = url + "/web/binary/download_document?model=comm.wizard.report&id=%s&field=excel_file&filename=%s" % (
            self.id, self.file_name)
        _log.info(file_url)
        return {
            'type': 'ir.actions.act_url',
            'url': file_url,
        }

    def ref_acc_report(self):
        _log.info(" GENERANDO REPORTE DE MOTOS.. ")
        if self.year:
            current_year = int(self.year)
        else:
            current_year = fields.Date().today().year
        _log.info("AÑO considerado :: %s " % current_year)

        if self.month_final:
            self.file_name = 'Refacciones y accesorios %s a %s de %s.xlsx' % (NUM_MONTHS[self.month_start], NUM_MONTHS[self.month_final], current_year)
            fp = io.BytesIO()
            months = self.create_month_range(self.month_start, self.month_final)
            domain = [
                ('current_month', 'in', months)
            ]
        else:
            self.file_name = 'Refacciones y accesorios %s-%s.xlsx' % (NUM_MONTHS[self.month_start], current_year)
            fp = io.BytesIO()
            domain = [
                ('current_month', '=', self.month_start)
            ]

        if not self.include_paid_comms:
            domain.append(('state', '=', "to_pay"))
        comm_ids_unfiltered = self.env['seller.commission'].search(domain)
        comm_ids = comm_ids_unfiltered.filtered(lambda cy: current_year == cy.create_date.year and cy.seller_id is not False)
        if not comm_ids:
            raise UserError("No se encontraron comisiones con los datos especificados.")
        # Mapeamos los colaboradores que tienen pendientes comisiones desde el módulo de ventas.
        seller_ids = comm_ids.mapped('seller_id')

        # Formación del reporte.
        workbook = xlsxwriter.Workbook(fp, {'in_memory': True})
        title = workbook.add_format(
            {'bold': True,
             'font_size': 18,
             'bg_color': 'white',
             'center_across': True
             })
        encabezados = workbook.add_format(
            {'bold': True,
             'font_size': 10,
             'bg_color': '#B7F9B0',
             'center_across': True
             })
        datas = workbook.add_format(
            {'bold': False,
             'font_size': 8,
             'bg_color': 'white',
             'center_across': True
             })
        datas2 = workbook.add_format(
            {'bold': False,
             'font_size': 8,
             'bg_color': 'yellow',
             'center_across': True
             })
        sheet = workbook.add_worksheet('%s' % "Refacciones & accesorios")

        vertical_offset_table = 3
        sheet.set_column(0, 1, 10)
        sheet.set_column(2, 2, 5)
        sheet.set_column(3, 3, 25)
        sheet.set_column(4, 5, 8)
        sheet.set_column(6, 6, 25)

        sheet.merge_range(1, 3, 2, 8, self.env.company.name, title)
        sheet.write(1, 1, fields.Date().today().strftime(DATE_FORMAT))

        sheet.write(vertical_offset_table, 0, '', encabezados)
        sheet.write(vertical_offset_table, 1, 'Nombre', encabezados)
        sheet.write(vertical_offset_table, 2, 'Facturas', encabezados)
        sheet.write(vertical_offset_table, 3, 'Piezas', encabezados)
        sheet.write(vertical_offset_table, 4, 'Importe', encabezados)
        sheet.write(vertical_offset_table, 5, '', encabezados)
        sheet.write(vertical_offset_table, 6, '', encabezados)
        sheet.write(vertical_offset_table, 7, '', encabezados)
        sheet.write(vertical_offset_table, 8, 'comisión', encabezados)
        sheet.write(vertical_offset_table, 9, 'Comisión total', encabezados)
        
        # Acumuladores
        row_pl = 1
        seller_commission_total = 0
        
        for seller in seller_ids:
            
            current_row = row_pl + vertical_offset_table
            seller_coms = comm_ids.filtered(lambda co: co.seller_id and co.seller_id.id == seller.id)
            seller_prelines_applied = seller_coms.mapped('preline_ids').filtered(lambda pl: pl.commission_line_id is not False and not pl.is_repair_sale)
            seller_inv_qty = len(seller_prelines_applied.mapped('invoice_id') or [])

            # Lineas de venta del vendedor. 
            original_selling_lines = self.env['repair.line'].search([('id', 'in', seller_prelines_applied.mapped('rec_id'))])
            product_qty_sold = sum(original_selling_lines.mapped('product_uom_qty'))
            amount_sold = sum(original_selling_lines.mapped('price_subtotal'))

            # Tabla
            sheet.write(current_row, 1, seller.name, datas)
            sheet.write(current_row, 2, seller_inv_qty, datas)
            sheet.write(current_row, 3, product_qty_sold, datas)
            sheet.write(current_row, 4, amount_sold, datas)

            sheet.write(current_row, " ", amount_sold, datas)
      
            row_pl += 1


        # Finalizado el reporte se construye el binario.
        workbook.close()
        fp.seek(0)
        self.excel_file = base64.encodestring(fp.getvalue())
        fp.close()
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        file_url = url + "/web/binary/download_document?model=comm.wizard.report&id=%s&field=excel_file&filename=%s" % (
            self.id, self.file_name)
        _log.info(file_url)
        return {
            'type': 'ir.actions.act_url',
            'url': file_url,
        }

    @api.model
    def create_month_range(self, ini, fin):
        """
        Método que crea un arreglo de numeros como char, dados inicio y fin.
        :param ini: string mes inicial
        :param fin: string mes final
        :return: array de meses (numeros como string)
        """
        ini_i = int(ini)
        fin_i = int(fin)
        if fin_i < ini_i:
            raise UserError("El mes final debe ser posterior al mes inicial")
        months_i = list(range(ini_i, fin_i+1))
        return list(map(str, months_i))

# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import AccessError, UserError, ValidationError
import logging
import io
import base64
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

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
    ], string="Mes", required=True)
    year = fields.Selection([
        ("2021", "2021"),
        ("2022", "2022"),
        ("2023", "2023"),
        ("2024", "2024")
    ], string="Año", required=True)
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
        _log.info(" Regresando reporte de mecánicos.. ")
        # Considerar que seleccionen el mismo mes o bien que seleccionen el primero o bien uno de los dos.
        self.file_name = 'Servicios %s a %s de %s.xlsx' % (NUM_MONTHS[self.month_start], NUM_MONTHS[self.month_final], self.year)
        fp = io.BytesIO()
        workbook = xlsxwriter.Workbook(fp, {'in_memory': True})
        encabezados = workbook.add_format(
            {'bold': 'True', 'font_size': 12, 'bg_color': '#B7F9B0', 'center_across': True})

        # Buscamos las comisiones de los mecánicos.
        # Agrupamos comisiones por mecánicos e iteramos las mismas.
        months = self.create_month_range(self.month_start, self.month_final)
        domain = [
            ('current_month', 'in', months)
        ]
        if not self.include_paid_comms:
            domain.append(('state', '=', "to_pay"))
        comm_ids = self.env['seller.commission'].search(domain)
        mechanic_ids = comm_ids.mapped('mechanic_id')
        _log.info(" MECANICOS .... :: :%s " % mechanic_ids)
        for mechanic in mechanic_ids:
            sheet = workbook.add_worksheet('%s' % mechanic.display_name)
            sheet.set_column(0, 0, 15)
            sheet.set_column(1, 1, 45)
            sheet.set_column(2, 2, 15)
            sheet.set_column(3, 5, 12)
            sheet.set_column(6, 8, 12)
            sheet.write(0, 0, 'Orden reparación', encabezados)
            sheet.write(0, 1, 'Fecha orden', encabezados)
            sheet.write(0, 2, 'Estado factura', encabezados)
            sheet.write(0, 3, 'Fecha factura', encabezados)
            sheet.write(0, 4, 'Venta tpv', encabezados)
            sheet.write(0, 5, 'Modelo', encabezados)
            sheet.write(0, 6, 'Servicio', encabezados)
            sheet.write(0, 7, 'Cantidad', encabezados)
            sheet.write(0, 8, 'P. Unitario', encabezados)
            sheet.write(0, 9, 'Subtotal', encabezados)
            sheet.write(0, 10, 'Regla comisión', encabezados)
            sheet.write(0, 11, 'Comisión', encabezados)
            total_comision = 0

            # Comisiones de mecánico.
            mechanic_coms = comm_ids.filtered(lambda co: co.mechanic_id and co.mechanic_id.id == mechanic.id)
            mc_prelines_applied = mechanic_coms.mapped('preline_ids').filtered(lambda pl: pl.commission_line_id is not False)
            row_pl = 1
            # Buscar las lineas relacionadas (rec_id) y en el ciclo abajo
            # las filtramos.

            clamount_total = 0
            _log.info("PRELINAS:: %s " % mc_prelines_applied)
            for mcpl in mc_prelines_applied:
                rol = self.env['repair.fee'].browse(mcpl.rec_id)
                # Calculo de la linea con la regla exacta. 
                if mcpl.commission_line_id.comm_rule.calc_method == "fixed":
                    clamount = rol.product_uom_qty * mcpl.commission_line_id.comm_rule.amount_factor
                else:
                    factor = mcpl.commission_line_id.comm_rule.amount_factor/100
                    clamount = mcpl.amount*factor
                clamount_total += clamount
                sheet.write(row_pl, 0, rol.repair_id.name)
                sheet.write(row_pl, 1, rol.repair_id.create_date)
                sheet.write(row_pl, 2, mcpl.invoice_id.state)
                sheet.write(row_pl, 3, mcpl.invoice_id.invoice_date)
                sheet.write(row_pl, 4, rol.repair_id.tpv_ids[0].name)
                sheet.write(row_pl, 5, rol.repair_id.product_id.name)
                sheet.write(row_pl, 6, rol.name)
                sheet.write(row_pl, 7, rol.product_uom_qty)
                sheet.write(row_pl, 8, rol.price_unit)
                sheet.write(row_pl, 9, mcpl.amount) # Subtotal
                sheet.write(row_pl,10, mcpl.commission_line_id.comm_rule.name) # Regla de comision
                sheet.write(row_pl, 11, clamount)
                row_pl += 1
            _log.info("Suma comision total::: %s " % clamount_total)

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
        self.file_name = 'Motocicletas %s a %s de %s.xlsx' % (
        NUM_MONTHS[self.month_start], NUM_MONTHS[self.month_final], self.year)
        fp = io.BytesIO()
        workbook = xlsxwriter.Workbook(fp, {'in_memory': True})
        encabezados = workbook.add_format(
            {'bold': 'True', 'font_size': 12, 'bg_color': '#B7F9B0', 'center_across': True})
        sheet = workbook.add_worksheet('Libro 1')
        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 45)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 5, 12)
        sheet.set_column(6, 8, 12)
        sheet.write(0, 0, 'Codigo', encabezados)
        sheet.write(0, 1, 'Descripción', encabezados)
        sheet.write(0, 2, 'Sucursal', encabezados)
        sheet.write(0, 3, 'Cantidad Teorica', encabezados)
        sheet.write(0, 4, 'Precio Unitario', encabezados)
        sheet.write(0, 5, 'Precio Total', encabezados)
        sheet.write(0, 6, 'Cantidad Real', encabezados)
        r = 2
        sheet.write(r, 0, "aaaaaaaaa")
        sheet.write(r, 1, "bbbbbbb")
        sheet.write(r, 2, "cccccccccc")
        sheet.write(r, 3, "dddddddddddd")
        sheet.write(r, 4, "eeeeeeee")
        sheet.write(r, 5, "dfff")
        sheet.write(r, 6, 'sss')

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
        _log.info("Generando reporte de accesorios y refacciones")
        self.file_name = 'Refacciones y accesorios %s a %s de %s.xlsx' % (
        NUM_MONTHS[self.month_start], NUM_MONTHS[self.month_final], self.year)
        fp = io.BytesIO()
        workbook = xlsxwriter.Workbook(fp, {'in_memory': True})
        encabezados = workbook.add_format(
            {'bold': 'True', 'font_size': 12, 'bg_color': '#B7F9B0', 'center_across': True})
        sheet = workbook.add_worksheet('Libro 1')
        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 45)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 5, 12)
        sheet.set_column(6, 8, 12)
        sheet.write(0, 0, 'Codigo', encabezados)
        sheet.write(0, 1, 'Descripción', encabezados)
        sheet.write(0, 2, 'Sucursal', encabezados)
        sheet.write(0, 3, 'Cantidad Teorica', encabezados)
        sheet.write(0, 4, 'Precio Unitario', encabezados)
        sheet.write(0, 5, 'Precio Total', encabezados)
        sheet.write(0, 6, 'Cantidad Real', encabezados)
        r = 2
        sheet.write(r, 0, "aaaaaaaaa")
        sheet.write(r, 1, "bbbbbbb")
        sheet.write(r, 2, "cccccccccc")
        sheet.write(r, 3, "dddddddddddd")
        sheet.write(r, 4, "eeeeeeee")
        sheet.write(r, 5, "dfff")
        sheet.write(r, 6, 'sss')

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

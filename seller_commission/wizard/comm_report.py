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

        self.file_name = 'Servicios %s a %s de %s.xlsx' % (NUM_MONTHS[self.month_start], NUM_MONTHS[self.month_final], self.year)
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

    def motos_report(self):
        _log.info(" GENERANDO REPORTE DE MOTOS.. ")
        return False

    def ref_acc_report(self):
        _log.info("Generando reporte de accesorios y refacciones")
        return False


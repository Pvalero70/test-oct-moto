# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

from datetime import datetime
from xml.dom import minidom

import base64
import logging
import json

_logger = logging.getLogger(__name__)

class PmgImportaCfdi(models.Model):
	_name="pmg.importa.cfdi"

	# https://gitlab.com/takluyver/zipfile36/-/blob/master/zipfile36.py
	
	name = fields.Char(string="Impoprtacion", default=lambda self: "{}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
	file_xml = fields.Binary(string="Cfdi")
	file_name = fields.Char('Nombre archivo', default='cfdi_proveedor.xml')
	lines = fields.One2many("pmg.importa.cfdi.line", "cfdi_id", "Cfdis Lines")
	lines_detail = fields.One2many("pmg.importa.cfdi.line.product", "cfdi_id", "Cfdis Products")
	state = fields.Selection([('draft', 'Pendiente'), ('ready', 'En proceso'), ('done', 'Completado')], string='Estatus', default='draft')

	def _get_xml_data(self, xml_str):

		doc = minidom.parseString(xml_str)

		data = {
			"comprobante" : {},
			"emisor" : {},
			"conceptos" : []
		}

		comprobante = doc.getElementsByTagName("cfdi:Comprobante")[0]
		data['comprobante']['serie'] = comprobante.getAttribute("Serie")
		data['comprobante']['folio'] = comprobante.getAttribute("Folio")
		data['comprobante']['fecha'] = comprobante.getAttribute("Fecha")
		data['comprobante']['forma_pago'] = comprobante.getAttribute("FormaPago")
		data['comprobante']['metodo_pago'] = comprobante.getAttribute("MetodoPago")
		data['comprobante']['expedicion'] = comprobante.getAttribute("LugarExpedicion")
		data['comprobante']['condiciones'] = comprobante.getAttribute("CondicionesDePago")
		data['comprobante']['moneda'] = comprobante.getAttribute("Moneda")
		data['comprobante']['subtotal'] = comprobante.getAttribute("SubTotal")
		data['comprobante']['total'] = comprobante.getAttribute("Total")

		complemento = comprobante.getElementsByTagName('tfd:TimbreFiscalDigital')[0]
		data['comprobante']['uuid'] = complemento.getAttribute('UUID')

		emisor = doc.getElementsByTagName("cfdi:Emisor")[0]
		rfc = emisor.getAttribute("Rfc")
		nombre = emisor.getAttribute("Nombre")
		data['emisor']['rfc'] = rfc
		data['emisor']['nombre'] = nombre

		conceptos = doc.getElementsByTagName("cfdi:Concepto")
		
		for concepto in conceptos:
			sku = concepto.getAttribute("NoIdentificacion")
			cantidad = concepto.getAttribute("Cantidad")
			descripcion = concepto.getAttribute("Descripcion")
			precio = concepto.getAttribute("ValorUnitario")
			descuento = concepto.getAttribute("Descuento")
			importe = concepto.getAttribute("Importe")

			concepto_data = {
				"sku" : sku,
				"cantidad" : cantidad,
				"descripcion" : descripcion,
				"precio" : precio,
				"importe" : importe,
				"descuento" : descuento
			}

			impuesto = concepto.getElementsByTagName("cfdi:Traslado")[0]
			tax_base = impuesto.getAttribute("Base")
			tax_code = impuesto.getAttribute("Impuesto")
			tax_rate = impuesto.getAttribute("TasaOCuota")
			tax_amount = impuesto.getAttribute("Importe")

			concepto_data["impuesto"] = {
				"tax_base" : tax_base,
				"tax_code" : tax_code,
				"tax_rate" : tax_rate,
				"tax_amount" : tax_amount
			}

			partes = concepto.getElementsByTagName("cfdi:Parte")
			if partes:
				parte_sku = partes[0].getAttribute("NoIdentificacion")
				concepto_data["parte"] = {
					"parte_sku" : parte_sku
				}
				# concepto_data['sku'] = parte_sku[:9]

			data['conceptos'].append(concepto_data)

		return data

	def _save_cfdi_data(self, rec, data):
		cfdi_data = []
		for record in data:
			new_cfdi = {
				"cfdi_id" : rec.id,
				"cfdi_emisor" : record.get('emisor', {}).get('nombre'),
				"cfdi_emisor_rfc" : record.get('emisor', {}).get('rfc'),
				"cfdi_uuid" : record.get('comprobante', {}).get('uuid'),
				"cfdi_fecha" : record.get('comprobante', {}).get('fecha'),
				"cfdi_serie" : record.get('comprobante', {}).get('serie'),
				"cfdi_folio" : record.get('comprobante', {}).get('folio'),
				"cfdi_subtotal" : record.get('comprobante', {}).get('subtotal'),
				"cfdi_total" : record.get('comprobante', {}).get('total'),
				"cfdi_moneda" : record.get('comprobante', {}).get('moneda'),
				"cfdi_data" : json.dumps(record),
				"cfdi_product_ids" : []
			}

			lista_conceptos = []
			for concepto in record.get('conceptos', []):
				nuevo_concepto = {
					"cfdi_id" : rec.id,
					"cfdi_product_sku" : concepto.get("sku"),
					"cfdi_product_description" : concepto.get("descripcion"),
					"cfdi_product_qty" : concepto.get("cantidad"),
					"cfdi_product_price" : concepto.get("precio"),
					"cfdi_product_discount" : concepto.get("descuento"),
					"cfdi_product_amount" : concepto.get("importe"),
					"cfdi_product_tax_code" : concepto.get("impuesto", {}).get('tax_code'),
					"cfdi_product_tax_base" : concepto.get("impuesto", {}).get('tax_base'),
					"cfdi_product_tax_rate" : concepto.get("impuesto", {}).get('tax_rate'),
					"cfdi_product_tax_amount" : concepto.get("impuesto", {}).get('tax_amount'),
					"cfdi_product_parte_sku" : concepto.get("parte", {}).get('parte_sku'),
					"cfdi_product_data" : json.dumps(concepto)

				}
				lista_conceptos.append((0, 0, nuevo_concepto))

			new_cfdi['cfdi_product_ids'] = lista_conceptos

			cfdi_data.append((0, 0, new_cfdi))

		if cfdi_data:
			_logger.info("################")
			_logger.info(cfdi_data)
			if rec.lines:
				rec.lines.unlink()
			if rec.lines_detail:
				rec.lines_detail.unlink()
			try:
				rec.lines = cfdi_data
			except Exception as e:
				_logger.exception(e)

	def _leer_xml(self):
		for rec in self:	
			xml_str = base64.decodestring(rec.file_xml)
			xml_str = xml_str.decode('utf-8')
			data = self._get_xml_data(xml_str)
			_logger.info(data)
			if data:
				try:
					self._save_cfdi_data(rec, [data])
				except Exception as e:
					_logger.exception(e)
				else:
					if not rec.name:
						rec.name = 'Importacion XML {}'.format(rec.name or datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

	def leer_archivo(self):
		for rec in self:
			if rec.file_xml:
				self._leer_xml()
			rec.state = 'ready'		
				
class PmgImportaCfdiLine(models.Model):
	_name="pmg.importa.cfdi.line"

	_rec_name = 'cfdi_uuid'

	file_xml = fields.Binary(string="Cfdi")
	file_name = fields.Char('Nombre archivo', default='cfdi_proveedor.xml')
	# cfdi_id = fields.Many2one("pmg.importa.cfdi", "CFDI")
	cfdi_data = fields.Text("CFDI Data")
	cfdi_uuid = fields.Char('UUID')
	cfdi_fecha = fields.Char('Fecha')
	cfdi_emisor = fields.Char('Emisor')
	cfdi_emisor_rfc = fields.Char('Emisor RFC')
	cfdi_serie = fields.Char('Serie')
	cfdi_folio = fields.Char('Folio')
	cfdi_fecha = fields.Char('Fecha')
	cfdi_subtotal = fields.Char('Subtotal')
	cfdi_total = fields.Char('Total')
	cfdi_moneda = fields.Char('Moneda')
	cfdi_product_ids = fields.One2many('pmg.importa.cfdi.line.product', 'line_id', 'Productos')
	cfdi_state = fields.Selection([('draft', 'Pendiente'),  ('ready', 'En proceso'), ('done', 'Completado')], string='Estatus', default='draft')
	cfdi_errors = fields.Text('Errores de Mapeo')

	def _get_xml_data(self, xml_str):

		doc = minidom.parseString(xml_str)

		data = {
			"comprobante" : {},
			"emisor" : {},
			"conceptos" : []
		}

		comprobante = doc.getElementsByTagName("cfdi:Comprobante")[0]
		data['comprobante']['serie'] = comprobante.getAttribute("Serie")
		data['comprobante']['folio'] = comprobante.getAttribute("Folio")
		data['comprobante']['fecha'] = comprobante.getAttribute("Fecha")
		data['comprobante']['forma_pago'] = comprobante.getAttribute("FormaPago")
		data['comprobante']['metodo_pago'] = comprobante.getAttribute("MetodoPago")
		data['comprobante']['expedicion'] = comprobante.getAttribute("LugarExpedicion")
		data['comprobante']['condiciones'] = comprobante.getAttribute("CondicionesDePago")
		data['comprobante']['moneda'] = comprobante.getAttribute("Moneda")
		data['comprobante']['subtotal'] = comprobante.getAttribute("SubTotal")
		data['comprobante']['total'] = comprobante.getAttribute("Total")

		complemento = comprobante.getElementsByTagName('tfd:TimbreFiscalDigital')[0]
		data['comprobante']['uuid'] = complemento.getAttribute('UUID')

		emisor = doc.getElementsByTagName("cfdi:Emisor")[0]
		rfc = emisor.getAttribute("Rfc")
		nombre = emisor.getAttribute("Nombre")
		data['emisor']['rfc'] = rfc
		data['emisor']['nombre'] = nombre

		conceptos = doc.getElementsByTagName("cfdi:Concepto")
		
		for concepto in conceptos:
			sku = concepto.getAttribute("NoIdentificacion")
			cantidad = concepto.getAttribute("Cantidad")
			descripcion = concepto.getAttribute("Descripcion")
			precio = concepto.getAttribute("ValorUnitario")
			descuento = concepto.getAttribute("Descuento")
			importe = concepto.getAttribute("Importe")

			concepto_data = {
				"sku" : sku,
				"cantidad" : cantidad,
				"descripcion" : descripcion,
				"precio" : precio,
				"importe" : importe,
				"descuento" : descuento
			}

			impuesto = concepto.getElementsByTagName("cfdi:Traslado")[0]
			tax_base = impuesto.getAttribute("Base")
			tax_code = impuesto.getAttribute("Impuesto")
			tax_rate = impuesto.getAttribute("TasaOCuota")
			tax_amount = impuesto.getAttribute("Importe")

			concepto_data["impuesto"] = {
				"tax_base" : tax_base,
				"tax_code" : tax_code,
				"tax_rate" : tax_rate,
				"tax_amount" : tax_amount
			}

			partes = concepto.getElementsByTagName("cfdi:Parte")
			if partes:
				parte_sku = partes[0].getAttribute("NoIdentificacion")
				concepto_data["parte"] = {
					"parte_sku" : parte_sku
				}
				# concepto_data['sku'] = parte_sku[:9]

			data['conceptos'].append(concepto_data)

		return data

	def _save_cfdi_data(self, rec, data):
		cfdi_data = []
		for record in data:
			new_cfdi = {
				# "cfdi_id" : rec.id,
				"cfdi_emisor" : record.get('emisor', {}).get('nombre'),
				"cfdi_emisor_rfc" : record.get('emisor', {}).get('rfc'),
				"cfdi_uuid" : record.get('comprobante', {}).get('uuid'),
				"cfdi_fecha" : record.get('comprobante', {}).get('fecha'),
				"cfdi_serie" : record.get('comprobante', {}).get('serie'),
				"cfdi_folio" : record.get('comprobante', {}).get('folio'),
				"cfdi_subtotal" : record.get('comprobante', {}).get('subtotal'),
				"cfdi_total" : record.get('comprobante', {}).get('total'),
				"cfdi_moneda" : record.get('comprobante', {}).get('moneda'),
				"cfdi_data" : json.dumps(record),
				"cfdi_product_ids" : []
			}

			lista_conceptos = []
			for concepto in record.get('conceptos', []):
				nuevo_concepto = {
					"cfdi_id" : rec.id,
					"cfdi_product_sku" : concepto.get("sku"),
					"cfdi_product_description" : concepto.get("descripcion"),
					"cfdi_product_qty" : concepto.get("cantidad"),
					"cfdi_product_price" : concepto.get("precio"),
					"cfdi_product_discount" : concepto.get("descuento"),
					"cfdi_product_amount" : concepto.get("importe"),
					"cfdi_product_tax_code" : concepto.get("impuesto", {}).get('tax_code'),
					"cfdi_product_tax_base" : concepto.get("impuesto", {}).get('tax_base'),
					"cfdi_product_tax_rate" : concepto.get("impuesto", {}).get('tax_rate'),
					"cfdi_product_tax_amount" : concepto.get("impuesto", {}).get('tax_amount'),
					"cfdi_product_parte_sku" : concepto.get("parte", {}).get('parte_sku'),
					"cfdi_product_data" : json.dumps(concepto)

				}
				lista_conceptos.append((0, 0, nuevo_concepto))

			new_cfdi['cfdi_product_ids'] = lista_conceptos

			cfdi_data.append((0, 0, new_cfdi))

		if cfdi_data:
			_logger.info("################")
			_logger.info(cfdi_data)
			# if rec.lines:
			# 	rec.lines.unlink()
			# if rec.lines_detail:
			# 	rec.lines_detail.unlink()
			try:
				rec.write(cfdi_data)
			except Exception as e:
				_logger.exception(e)

	def _leer_xml(self):
		for rec in self:	
			xml_str = base64.decodestring(rec.file_xml)
			xml_str = xml_str.decode('utf-8')
			data = self._get_xml_data(xml_str)
			_logger.info(data)
			if data:
				try:
					self._save_cfdi_data(rec, [data])
				except Exception as e:
					_logger.exception(e)
				else:
					if not rec.name:
						rec.name = 'Importacion XML {}'.format(rec.name or datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

	def leer_archivo(self):
		for rec in self:
			if rec.file_xml:
				self._leer_xml()
			rec.cfdi_state = 'ready'		

class PmgImportaCfdiLineProduct(models.Model):
	_name="pmg.importa.cfdi.line.product"

	_rec_name = 'cfdi_product_sku'
	
	cfdi_id = fields.Many2one("pmg.importa.cfdi", "CFDI")
	line_id = fields.Many2one("pmg.importa.cfdi.line", "CFDI Line")
	cfdi_product_data = fields.Text("CFDI Product Data")
	cfdi_product_id = fields.Many2one('product.product', 'Producto')
	cfdi_product_sku = fields.Char('SKU Proveedor')
	cfdi_product_description = fields.Char('Description')
	cfdi_product_qty = fields.Char('Quantity')
	cfdi_product_price = fields.Char('Price')
	cfdi_product_discount = fields.Char('Descuento')
	cfdi_product_amount = fields.Char('Amount')
	cfdi_product_tax_code = fields.Char('Tax Code')
	cfdi_product_tax_base = fields.Char('Base')
	cfdi_product_tax_rate = fields.Char('Rate')
	cfdi_product_tax_amount = fields.Char('Tax Amount')
	cfdi_product_parte_sku = fields.Char('Parte Sku')

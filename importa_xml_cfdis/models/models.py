# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

from datetime import datetime
from xml.dom import minidom

import base64
import logging
import json

_logger = logging.getLogger(__name__)

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
	
	partner_id = fields.Many2one('res.partner', 'Proveedor')
	purchase_id = fields.Many2one('purchase.order', 'Orden Compra')

	cfdi_serie = fields.Char('Serie')
	cfdi_folio = fields.Char('Folio')
	cfdi_fecha = fields.Char('Fecha')
	cfdi_subtotal = fields.Char('Subtotal')
	cfdi_total = fields.Char('Total')
	cfdi_moneda = fields.Char('Moneda')
	cfdi_product_ids = fields.One2many('pmg.importa.cfdi.line.product', 'line_id', 'Productos')
	state = fields.Selection([('draft', 'Pendiente'),  ('ready', 'En proceso'), ('done', 'Completado')], string='Estatus', default='draft')
	cfdi_errors = fields.Text('Errores de Mapeo')
	cfdi_adenda = fields.Many2one('pmg.importa.cfdi.line.adenda', 'Adenda')

	def getNodeText(self, node):

		nodelist = node.childNodes
		result = []
		for node in nodelist:
			if node.nodeType == node.TEXT_NODE:
				result.append(node.data)
		return ''.join(result)

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

		chasis = ''
		adenda_chasis = comprobante.getElementsByTagName('ade:CHASIS')
		if adenda_chasis:
			chasis = self.getNodeText(adenda_chasis[0])

		number = ''
		adenda_number = comprobante.getElementsByTagName('ade:ENGIENERNUMBER')
		if adenda_number:
			number = self.getNodeText(adenda_number[0])

		clave_color = ''
		adenda_clave_color = comprobante.getElementsByTagName('ade:CVECOLOREXT')
		if adenda_clave_color:
			clave_color = self.getNodeText(adenda_clave_color[0])

		color = ''
		adenda_color = comprobante.getElementsByTagName('ade:DESCCOLOREXT')
		if adenda_color:
			color = self.getNodeText(adenda_color[0])

		adenda_data = {
			'adenda_chasis' : chasis,
			'adenda_numero' : number,
			'adenda_clave_color' : clave_color,
			'adenda_nombre_color' : color
		}
		data['adenda'] = adenda_data
		_logger.info("### ADENDA ###")
		_logger.info(adenda_data)
		_logger.info('#########')
		_logger.info('#########')
		_logger.info('#########')

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
					# "cfdi_id" : rec.id,
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
					# "cfdi_product_parte_sku" : concepto.get("parte", {}).get('parte_sku'),
					"cfdi_product_data" : json.dumps(concepto)

				}
				lista_conceptos.append((0, 0, nuevo_concepto))

			new_cfdi['cfdi_product_ids'] = lista_conceptos

			_logger.info("################")
			_logger.info(new_cfdi)
			# if rec.lines:
			# 	rec.lines.unlink()
			# if rec.lines_detail:
			# 	rec.lines_detail.unlink()

			try:
				adenda_id = self.env['pmg.importa.cfdi.line.adenda'].create({
					'adenda_chasis' : record.get('adenda', {}).get('adenda_chasis', ''),
					'adenda_numero' : record.get('adenda', {}).get('adenda_numero', ''),
					'adenda_clave_color' : record.get('adenda', {}).get('adenda_clave_color', ''),
					'adenda_nombre_color' : record.get('adenda', {}).get('adenda_nombre_color', '')
				})
			except Exception as e:
				_logger.exception(e)
			else:
				new_cfdi['cfdi_adenda'] = adenda_id

			try:
				rec.write(new_cfdi)
			except Exception as e:
				_logger.exception(e)
				

	def _leer_xml(self):
		for rec in self:	
			xml_str = base64.decodebytes(rec.file_xml)
			xml_str = xml_str.decode('utf-8')
			data = self._get_xml_data(xml_str)
			_logger.info(data)
			if data:
				try:
					self._save_cfdi_data(rec, [data])
				except Exception as e:
					_logger.exception(e)
				else:
					if not rec.file_name:
						rec.file_name = 'Importacion XML {}'.format(rec.name or datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

	def leer_description(self):

		for rec in self:
			for product in rec.cfdi_product_ids:
				_logger.info("## PRODUCT DATA ##")
				_logger.info(product.cfdi_product_description)
				sku = product.cfdi_product_sku
				descr = product.cfdi_product_description
				descr_words = descr.split(" ")
				_logger.info(descr_words)

				lista_busqueda = ['NIV', 'MOTOR', 'COLOR']
				not_found = False
				for word in lista_busqueda:
					if word not in descr_words:
						_logger.info('Not Found')
						not_found = True
						break

				if not_found:
					product.write({"cfdi_product_clave_prod" : sku})
					continue

				data = {}
				for word in lista_busqueda:
					index = descr_words.index(word)
					value = descr_words[index+1]
					data[word] = value
					_logger.info(f'{data[word]}')

				product.write({
					"cfdi_product_clave_prod" : sku,
					"cfdi_product_chasis" : data.get('NIV', ''),
					"cfdi_product_numero" : data.get('MOTOR', ''),
					"cfdi_product_clave_color" : data.get('COLOR', ''),
					"cfdi_product_nombre_color" : data.get('COLOR', ''),
				})

	def leer_description_solomoto(self):

		for rec in self:
			for product in rec.cfdi_product_ids:
				_logger.info("## PRODUCT DATA ##")
				_logger.info(product.cfdi_product_description)
				descr = product.cfdi_product_description

				descr_list = descr.split(" ")

				descr_data = []
				if descr_list:
					descr_data = [el.strip() for el in descr_list if el]
					_logger.info(descr_data)

				if len(descr_data) == 3:
					
					# _logger.info("Len: 3")
					# if len(descr_data[-1]) == 11 and len(descr_data[-2]) == 4:
					_logger.info("Coincidencia..")
					numero_motor = descr_data[-1]
					_logger.info(f'Motor: {numero_motor}')
					sku = descr_data[-2]
					_logger.info(f'Sku: {sku}')
					numero_serie = product.cfdi_product_sku
					_logger.info(f'Serie: {numero_serie}')

					product.write({
						"cfdi_product_clave_prod" : sku,
						"cfdi_product_chasis" : numero_serie,
						"cfdi_product_numero" : numero_motor,
						
					})

	def leer_description_jurgen(self):

		for rec in self:
			
			adenda = rec.cfdi_adenda

			numero_serie = adenda.adenda_chasis
			_logger.info(numero_serie)

			numero_motor = adenda.adenda_numero
			_logger.info(numero_motor)

			clave_color = adenda.adenda_clave_color
			_logger.info(clave_color)

			nombre_color = adenda.adenda_nombre_color
			_logger.info(nombre_color)

			for product in rec.cfdi_product_ids:
				
				sku = product.cfdi_product_sku
				
				product.write({
					"cfdi_product_chasis" : numero_serie,
					"cfdi_product_numero" : numero_motor,
					"cfdi_product_clave_color" : clave_color,
					"cfdi_product_nombre_color" : nombre_color,
					"cfdi_product_clave_prod" : sku,
				})
					
	def leer_archivo(self):
		for rec in self:
			if rec.file_xml:
				self._leer_xml()

				if rec.cfdi_emisor_rfc == "KME931015PC0":
					self.leer_description()

				elif rec.cfdi_emisor_rfc == "BME940711FR5":
					self.leer_description_jurgen()

				elif rec.cfdi_emisor_rfc == "YMM9105032FA":
					self.leer_description_solomoto()

				self.mapear_proveedor()

			rec.state = 'ready'

	def mapear_proveedor(self):

		for rec in self:

			if rec.cfdi_emisor_rfc:
				rfc_proveedor = rec.cfdi_emisor_rfc
				partner = self.env['res.partner'].search([('vat', '=', rfc_proveedor)], limit=1)

				if partner:
					rec.partner_id = partner.id

					lista_proveedores = self.env['product.supplierinfo']

					for line in rec.cfdi_product_ids:

						product_sku = line.cfdi_product_clave_prod

						res = lista_proveedores.search([('name', '=', partner.id), ('product_code', '=', product_sku)], limit=1)

						if res:
							_logger.info(res.id)
							_logger.info(res.product_id.id)
							_logger.info(res.product_tmpl_id.id)
							prod = res.product_id
							tmpl = res.product_tmpl_id
							if not prod:
								prod = self.env['product.product'].search([('product_tmpl_id', '=', tmpl.id)], limit=1)
							line.write({'cfdi_product_id' : prod.id, 'cfdi_product_state' : 'mapped'})
						else:
							line.write({'cfdi_product_state' : 'error'})

class PmgImportaCfdiAdenda(models.Model):
	_name = 'pmg.importa.cfdi.line.adenda'

	adenda_chasis = fields.Char('Chasis')
	adenda_numero = fields.Char('Numero')
	adenda_clave_color = fields.Char('Clave Color')
	adenda_nombre_color = fields.Char('Color')



class PmgImportaCfdiLineProduct(models.Model):
	_name="pmg.importa.cfdi.line.product"

	_rec_name = 'cfdi_product_sku'
	
	# cfdi_id = fields.Many2one("pmg.importa.cfdi", "CFDI")
	line_id = fields.Many2one("pmg.importa.cfdi.line", "CFDI Line")
	cfdi_product_data = fields.Text("CFDI Product Data")
	cfdi_product_id = fields.Many2one('product.product', 'Producto')
	cfdi_product_sku = fields.Char('No Identificacion')
	cfdi_product_description = fields.Char('Description')
	cfdi_product_qty = fields.Char('Quantity')
	cfdi_product_price = fields.Char('Price')
	cfdi_product_discount = fields.Char('Descuento')
	cfdi_product_amount = fields.Char('Amount')
	cfdi_product_tax_code = fields.Char('Tax Code')
	cfdi_product_tax_base = fields.Char('Base')
	cfdi_product_tax_rate = fields.Char('Rate')
	cfdi_product_tax_amount = fields.Char('Tax Amount')
	# cfdi_product_parte_sku = fields.Char('Parte Sku')
	cfdi_product_clave_prod = fields.Char('Clave Producto')
	cfdi_product_chasis = fields.Char('Numero Serie')
	cfdi_product_numero = fields.Char('Numero Motor')
	cfdi_product_clave_color = fields.Char('Clave Color')
	cfdi_product_nombre_color = fields.Char('Color')
	cfdi_product_state = fields.Selection([
		('pending', 'Pendiente'),
		('mapped', 'Mapeado'),
		('error', 'No encontrado')
	], string='Estatus', default='pending')

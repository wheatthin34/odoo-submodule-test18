# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields


class StockMove(models.Model):
    """Extend 'stock.move' model to add custom functionality."""

    _inherit = "stock.move"
    _description = "Stock Move"

    stock_picking_ids = fields.Many2many("stock.picking", string="Receipts")

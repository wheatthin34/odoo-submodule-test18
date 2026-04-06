# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    internal_transfer_kanban_id = fields.Many2one(
        "stock.picking.type", "Internal Transfer Type for Kanban"
    )

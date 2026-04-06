# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    internal_transfer_kanban_id = fields.Many2one(
        "stock.picking.type", "Internal Transfer Type for Kanban"
    )

# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields


class ProductTemplate(models.Model):
    """Class Inherit for store kanban details in product."""

    _inherit = "product.template"

    kfm_ids = fields.One2many(
        "mrp.kanban.reordering",
        "product_tmpl_id",
        string="Kanban From Manufacturing"
    )
    krr_ids = fields.One2many(
        "kanban.reordering",
        "product_tmpl_id",
        string="Kanban Re-Ordering"
    )

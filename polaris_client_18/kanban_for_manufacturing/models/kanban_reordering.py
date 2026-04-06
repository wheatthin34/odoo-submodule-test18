# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class KanbanReordering(models.Model):
    """Class for kanban Re-Ordering Rules."""

    _name = "kanban.reordering"
    _description = "Kanban Reordering"

    name = fields.Char(
        string="Name", required=True, default=lambda self: _("New"), copy=False
    )
    product_id = fields.Many2one("product.product", string="Product", required=True)
    product_tmpl_id = fields.Many2one(
        "product.template", related="product_id.product_tmpl_id", store=True
    )
    pricelist_id = fields.Many2one(
        "product.supplierinfo", string="Pricelist", required=True
    )
    reorder_qty = fields.Char(string="Reorder Quantity")
    minimum_qty = fields.Char(string="Minimum Quantity")
    automatic_confirm = fields.Boolean(string="Confirm RFQ automatically?")
    barcode = fields.Char(string="Barcode", copy=False, default=lambda self: _("New"))
    target_location_id = fields.Many2one("stock.location", string="Target Location")
    card = fields.Integer(string="Card")
    card_count = fields.Integer(string="Card Count")

    _sql_constraints = [
        (
            "barcode_uniq",
            "unique(barcode)",
            "A barcode can only be assigned to one Kanban Reordering rule !",
        ),
    ]

    @api.model
    def default_get(self, fields):
        """
        Override the default_get method to pre-fill the 'product_id' field based on context.

        Args:
            fields (list): List of fields to fetch default values for.

        Returns:
            dict: A dictionary of field names and their default values.
        """
        res = super(KanbanReordering, self).default_get(fields)
        if self._context.get("krr_product_id"):
            product_recs = self.env["product.product"].search(
                [("product_tmpl_id", "=", self._context.get("krr_product_id"))], limit=1
            )
            if product_recs:
                res["product_id"] = product_recs.id
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override the create method to assign default sequences to 'name' and 'barcode' fields.

        Args:
            vals_list (list): A list of dictionaries containing the values for the records to create.

        Returns:
            recordset: The newly created record(s) as an Odoo recordset.
        """
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "kanban.reordering.name"
                ) or _("New")
            if vals.get("barcode", _("New")) == _("New"):
                vals["barcode"] = self.env["ir.sequence"].next_by_code(
                    "kanban.reordering.barcode"
                ) or _("New")
        return super(KanbanReordering, self).create(vals_list)

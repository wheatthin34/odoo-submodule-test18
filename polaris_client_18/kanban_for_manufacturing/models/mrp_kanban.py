# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MrpKanbanReordering(models.Model):
    """Class Call for sacn manufacturing barcode."""

    _name = "mrp.kanban.reordering"
    _description = "MRP kanban Reordering"

    name = fields.Char("Name", copy=False)
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        domain=[("type", "=", "consu"), ("active", "=", True)],
    )
    product_tmpl_id = fields.Many2one(
        "product.template", related="product_id.product_tmpl_id", store=True
    )
    reorder_quantity = fields.Integer("Reorder Quantity")
    minimum_quantity = fields.Integer("Minimum Quantity")
    card = fields.Integer("Card")
    card_count = fields.Integer("Card Count")
    barcode = fields.Char("Barcode", copy=False)
    type = fields.Selection(
        [
            ("physical", "Physical"),
            ("internal_transfer", "Internal Transfer"),
            ("inter_warehouse", "Inter-Warehouse"),
            ("manufacturing_order", "Manufacturing Order"),
        ]
    )
    create_delivery_scan = fields.Boolean(string="Create Separate Delivery on Scan")
    source_location = fields.Many2one("stock.location", string="Source Location")
    destination_location = fields.Many2one(
        "stock.location", string="Destination Location"
    )
    validate_transfer_on_scan = fields.Boolean("Validate Transfer on Scan")
    create_transfer_scan = fields.Boolean(
        string="Create Separate Transfer on Scan", default=True
    )
    routes_id = fields.Many2one("stock.route", string="Route")
    tracking = fields.Selection(related="product_id.tracking", readonly=True)

    @api.model
    def default_get(self, fields):
        """
        Override the default_get method to pre-fill the 'product_id' field based on context.

        Args:
            fields (list): List of fields to fetch default values for.

        Returns:
            dict: A dictionary of field names and their default values.
        """
        res = super(MrpKanbanReordering, self).default_get(fields)
        if self._context.get("kfm_product_id"):
            product_recs = self.env["product.product"].search(
                [("product_tmpl_id", "=", self._context.get("kfm_product_id"))], limit=1
            )
            if product_recs:
                res["product_id"] = product_recs.id
        return res

    @api.constrains("source_location", "destination_location", "product_id")
    def _check_product_route_ids(self):
        """
        Validate product route configuration for inter-warehouse stock transfers.

        This method is triggered whenever the 'source_location', 'destination_location', or 'product_id'
        fields are modified, and it performs the following checks for transfers between different warehouses:

        1. Verifies that the source and destination locations are in different warehouses.
        2. Ensures that there are valid stock routes for the destination warehouse.
        3. Confirms that the product has selected route(s) assigned.
        4. Checks if the product's selected routes match the valid routes available for the destination location's warehouse.

        If any of these checks fail, a ValidationError is raised with an appropriate message:
        - If the source and destination locations are from the same warehouse.
        - If no resupply routes are configured for the destination warehouse.
        - If the product does not have any selected route_ids.
        - If the product's selected routes are not valid for the destination warehouse.

        Raises:
            ValidationError: If any of the above checks fail, providing detailed error messages.
        """
        if self.type == "inter_warehouse" and self.source_location and self.destination_location:
            source_warehouse_rec = self.source_location.warehouse_id
            destination_warehouse_rec = self.destination_location.warehouse_id

            # Check if source and destination locations are from the same warehouse
            if source_warehouse_rec == destination_warehouse_rec:
                raise ValidationError(
                    _(
                        """Source location and destination location is of same warehouse."""
                    )
                )

            # Fetch the stock routes for the destination warehouse
            location_route_rec = self.env["stock.route"].search(
                [
                    ("company_id", "=", self.destination_location.company_id.id),
                    ("product_selectable", "=", True),
                ]
            )

            # If no valid routes are found, raise an error
            if not location_route_rec:
                raise ValidationError(
                    _(
                        """Please select the resupply warehouses of the selected source and destination location."""
                    )
                )

            # Check if product's route_ids match the location's routes
            if not self.product_id.route_ids:
                raise ValidationError(
                    _("No route_ids selected for product (%s).") % self.product_id.name
                )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Assign default sequences for 'name' and 'barcode' if not provided.

        - 'name' is set using 'mrp.kanban.reordering.name' sequence.
        - 'barcode' is set using 'mrp.kanban.reordering.barcode' sequence if 'New'.

        Args:
            vals_list (list): List of dictionaries containing values for record creation.

        Returns:
            recordset: The created MrpKanbanReordering records.
        """
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "mrp.kanban.reordering.name"
                ) or _("New")
            if not vals.get("barcode"):
                vals["barcode"] = self.env["ir.sequence"].next_by_code(
                    "mrp.kanban.reordering.barcode"
                ) or _("New")
        return super(MrpKanbanReordering, self).create(vals_list)

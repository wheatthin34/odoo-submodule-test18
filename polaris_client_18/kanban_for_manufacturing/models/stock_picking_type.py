# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, models, fields
from odoo.exceptions import ValidationError


class StockPickingType(models.Model):
    """Extend 'stock.picking.type' model to add a new field and validation logic."""

    _inherit = "stock.picking.type"

    inter_warehouse = fields.Boolean(string="Inter-Warehouse")

    @api.constrains("inter_warehouse")
    def check_inter_warehouse(self):
        """
        Ensure that only one inter-warehouse picking type exists for a given warehouse and operation code.

        This method raises a validation error if an inter-warehouse picking type is already created
        for the same warehouse and operation code. The user will be prompted to either change the warehouse
        or modify the operation type.

        Raises:
        ValidationError: If more than one inter-warehouse picking type exists for the same warehouse
        and operation code.
        """
        if self.inter_warehouse:
            # Search for other inter-warehouse picking types with the same warehouse and operation code
            stock_picking_type_rec = self.env["stock.picking.type"].search(
                [
                    ("warehouse_id", "=", self.warehouse_id.id),
                    ("code", "=", self.code),
                    ("inter_warehouse", "=", True),
                ]
            )
            # If more than one record is found, raise a validation error
            if len(stock_picking_type_rec) > 1:
                raise ValidationError(
                    (
                        """Inter-warehouse of this record is already created.Change the warehouse or change the type of operation."""
                    )
                )

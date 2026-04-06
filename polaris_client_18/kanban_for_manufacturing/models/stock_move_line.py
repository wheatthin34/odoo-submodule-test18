# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models


class StockMoveLine(models.Model):
    """Extend 'stock.move.line' model to add custom functionality."""

    _inherit = "stock.move.line"
    _description = "Stock Move Lines"

    def get_picking(self):
        """
        Retrieve the list of receipt numbers associated with the current stock move line.

        This method fetches the names (receipt numbers) of the stock pickings related to 
        the stock move of this line.

        Returns:
            list: A list of receipt numbers (names) associated with the stock move.
        """
        # List comprehension for fetching receipt names
        receipts = [recipt.name for recipt in self.move_id.stock_picking_ids]
        return receipts


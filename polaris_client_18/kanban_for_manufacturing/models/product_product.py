# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, models


class ProductProduct(models.Model):
    """Inherit the product.product model to add custom search functionality."""

    _inherit = "product.product"

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        """
        Custom search method to return products of the selected type for Kanban card view.
        
        Args:
            name (str): The name or part of the name to search for.
            args (list, optional): Additional domain filters to apply.
            operator (str, optional): The comparison operator to use (default is 'ilike').
            limit (int, optional): The maximum number of records to return (default is 100).

        Returns:
            list: A list of matching products based on the search criteria.
        """
        # Initialize domain if not passed in args
        args = args or []

        # Add a domain filter if the context contains 'type' as 'manufacturing_order'
        if self._context.get("type") == "manufacturing_order":
            domain = [
                ("bom_ids", "!=", False),  # Products with associated BOM
                ("bom_ids.active", "=", True),  # Only active BOMs
                ("bom_ids.type", "=", "normal"),  # BOM of type 'normal'
            ]
            args += domain  # Append to the existing filters

        # Perform the search with the constructed domain
        return super(ProductProduct, self).name_search(
            name, args=args, operator=operator, limit=limit
        )
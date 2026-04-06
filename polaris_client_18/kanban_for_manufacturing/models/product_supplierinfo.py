# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, models


class ProductSupplierinfo(models.Model):
    """Extend 'product.supplierinfo' model to add custom search and name generation logic."""

    _inherit = "product.supplierinfo"

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        """
        Perform a search for supplier information records based on the product name
        or product code.

        Args:
            name (str): The name or product code to search for.
            args (list): Additional domain filters to apply.
            operator (str): The operator to use for the search (default is 'ilike').
            limit (int): The maximum number of records to return.

        Returns:
            list: A list of tuples containing the record ID and display name.
        """
        args = args or []
        domain = []
        if name:
            domain = ["|", ("partner_id", operator, name),
                ("product_code", operator, name)
            ]
        # Search and return the records based on the generated domain
        pricelist_recs = self.search(domain + args, limit=limit)
        return pricelist_recs.name_get()

    def name_get(self):
        """
        Generate a display name for supplier info records, combining
        partner name, product name, product code, and price.

        Returns:
            list: A list of tuples containing record IDs and their corresponding display names.
        """
        res = []
        for pricelist_rec in self:
            name_parts = [pricelist_rec.partner_id.name]
            if pricelist_rec.product_name:
                name_parts.append(pricelist_rec.product_name)
            if pricelist_rec.product_code:
                name_parts.append(pricelist_rec.product_code)
            if pricelist_rec.price:
                name_parts.append(str(pricelist_rec.price))

            # Join the parts with ' - ' and add to result
            res.append((pricelist_rec.id, " - ".join(name_parts)))
        return res

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        """
        Extend the search method to filter records by the selected product if
        a context key 'kanban_pricelist' is present.

        Args:
            domain (list): The search domain to apply.
            offset (int): The starting index for the results.
            limit (int): The maximum number of records to return.
            order (str): The sorting order of the results.

        Returns:
            recordset: A recordset of 'product.supplierinfo' matching the search criteria.
        """
        context = self._context
        if "kanban_pricelist" in context:
            product_rec = self.env["product.product"].browse(
                [context.get("kanban_pricelist")]
            )
            domain += [("product_tmpl_id", "=", product_rec.product_tmpl_id.id)]
        return super(ProductSupplierinfo, self)._search(
            domain=domain,
            offset=offset,
            limit=limit,
            order=order,
        )

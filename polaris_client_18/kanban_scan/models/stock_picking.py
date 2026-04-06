# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, models, fields


class Picking(models.Model):
    """Extend 'stock.picking' model to add custom field and barcode matching logic."""

    _inherit = "stock.picking"

    picking_status = fields.Char(string="Picking Status")

    @api.model
    def match_barcode(self, barcode):
        """Function call for scan receipt from barcode scanning screen."""
        """
        Match and return receipt details based on the scanning screen.

        This method is intended to be used by the barcode scanning screen to identify
        a stock picking (receipt) based on its name (barcode).

        Args:
            barcode (str): The barcode to match.

        Returns:
            dict: Dictionary containing receipt record info and details list,
                  or False if no match is found.
        """
        receipt_rec = self.search([("name", "=", barcode)], limit=1)
        if receipt_rec:
            receipt_dict = {
                "receipt_record_id": receipt_rec.id,
                "source": receipt_rec.origin,
                "receipt_list": [
                    {
                        "receipt_id": receipt_rec.id,
                        "picking_type_id": receipt_rec.picking_type_id.name,
                        "name": receipt_rec.name,
                        "source_location": receipt_rec.location_id.display_name,
                        "destination_location": receipt_rec.picking_type_id.default_location_dest_id.display_name,
                        "schedule_date": receipt_rec.scheduled_date,
                        "state": receipt_rec.state,
                    }
                ],
            }
            return receipt_dict
        return False

    @api.model
    def confirm_receipt_data(self, receipt_record_id):
        """
        Validate the stock receipt if it is not cancelled or already done.

        Args:
            receipt_record_id (int): ID of the stock.picking record to validate.

        Returns:
            dict: A dictionary indicating success or failure:
                {
                    "receipt_value": True/False,
                    "stock_receipt": <ID>,         # if success
                    "stock_receipt_name": <Name>,  # if success
                }
        """
        receipt_rec = self.browse(receipt_record_id)
        if receipt_rec.state not in ("cancel", "done"):
            for moves in receipt_rec.move_ids:
                moves.update({"quantity": moves.product_uom_qty})
            receipt_rec.with_context({"system_validation": True}).button_validate()
            return {
                "receipt_value": True,
                "stock_receipt": receipt_rec.id,
                "stock_receipt_name": receipt_rec.name,
            }
        return {
            "receipt_value": False,
        }

# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, models, fields


class KanbanReordering(models.Model):
    """Class for kanban Re-Ordering Rules."""

    _inherit = "kanban.reordering"

    @api.model
    def match_barcode(self, barcode):
        """Function Call for Metch Barcode which scab by user."""
        reordering_rec = self.search([("barcode", "=", barcode)])
        PURCHASE_STATE_LABELS = {
            'draft': 'RFQ',
            'sent': 'RFQ Sent',
            'to approve': 'To Approve',
            'purchase': 'Purchase Order',
            'done': 'Locked',
            'cancel': 'Cancelled',
        }

        if reordering_rec:

            kkr_dict = {
                "kkr_id": reordering_rec.id,
                "name": reordering_rec.name,
                "product": reordering_rec.product_id.name,
                "vendor": reordering_rec.pricelist_id.partner_id.name,
                "quantity": reordering_rec.reorder_qty or 0,
            }
            # Purhchase Order
            purchase_list = []

            # RFQ
            rfq_rec = self.env["purchase.order"].search(
                [
                    ("partner_id", "=", reordering_rec.pricelist_id.partner_id.id),
                    ("state", "in", ["draft", "sent"]),
                ],
                order="id desc",
            )
            if rfq_rec:
                rfq_line_recs = rfq_rec.mapped("order_line").filtered(
                    lambda t: t.product_id.id == reordering_rec.product_id.id
                )
                kkr_dict.update(
                    {
                        "purchase_id": rfq_rec[0].id,
                        "purchase_exist": True,
                        "current_purchase_order_rec_name": rfq_rec[0].name,
                    }
                )
                for rfq_line_rec in rfq_line_recs:
                    purchase_list.append(
                        {
                            "purchase_type": "RFQ",
                            "purchase_number": rfq_line_rec.order_id.name,
                            "purchase_id": rfq_line_rec.order_id.id,
                            "purchase_vendor": rfq_line_rec.order_id.partner_id.name,
                            "purchase_qty": rfq_line_rec.product_qty,
                            "received_qty": rfq_line_rec.qty_received,
                            "purchase_scheduled_date": rfq_line_rec.date_planned,
                            "purchase_state": PURCHASE_STATE_LABELS.get(rfq_line_rec.order_id.state, rfq_line_rec.order_id.state),
                        }
                    )
            # Purchase Order
            purchase_recs = self.env["purchase.order"].search(
                [
                    ("partner_id", "=", reordering_rec.pricelist_id.partner_id.id),
                    ("state", "not in", ["draft", "sent", "done", "cancel"]),
                    ("order_line.product_id", "=", reordering_rec.product_id.id),
                ]
            )

            if purchase_recs:
                po_line_recs = purchase_recs.mapped("order_line").filtered(
                    lambda t: t.product_id.id == reordering_rec.product_id.id
                )
                for po_line_rec in po_line_recs:
                    purchase_list.append(
                        {
                            "purchase_type": "PO",
                            "purchase_number": po_line_rec.order_id.name,
                            "purchase_vendor": po_line_rec.order_id.partner_id.name,
                            "purchase_id": po_line_rec.order_id.id,
                            "purchase_qty": po_line_rec.product_qty,
                            "received_qty": po_line_rec.qty_received,
                            "purchase_scheduled_date": po_line_rec.date_planned,
                            "purchase_state": PURCHASE_STATE_LABELS.get(po_line_rec.order_id.state, po_line_rec.order_id.state),
                        }
                    )
            kkr_dict.update({"purchase_list": purchase_list})
            return kkr_dict
        else:
            return False

    @api.model
    def create_po(self, kkr_id):
        kkr_rec = self.browse(kkr_id)

        vendor = kkr_rec.pricelist_id.partner_id
        product = kkr_rec.product_id

        # 1Find existing Draft/Sent PO
        existing_po = self.env["purchase.order"].search(
            [
                ("partner_id", "=", vendor.id),
                ("state", "in", ["draft", "sent"]),
            ],
            order="id desc",
            limit=1,
        )

        # If not found → create new PO
        if not existing_po:
            po_order = self.env["purchase.order"].create({
                "partner_id": vendor.id,
                "company_id": self.env.company.id,
            })
        else:
            po_order = existing_po

        # 3Check if same product already exists in PO
        existing_line = po_order.order_line.filtered(
            lambda l: l.product_id.id == product.id
        )

        if existing_line:
            # Increase quantity (NO duplicate line)
            existing_line.write({
                "product_qty": existing_line.product_qty + kkr_rec.reorder_qty
            })
        else:
            # Add new product line
            self.env["purchase.order.line"].create({
                "order_id": po_order.id,
                "product_id": product.id,
                "product_qty": kkr_rec.reorder_qty,
                "price_unit": kkr_rec.pricelist_id.price,
                "date_planned": fields.Datetime.now(),
                "name": product.display_name,
            })

        # Auto confirm if needed
        if kkr_rec.automatic_confirm and po_order.state in ["draft", "sent"]:
            po_order.button_confirm()

        return [po_order.id, po_order.name]

    @api.model
    def update_po(self, purchase_id, kkr_id):
        """Update Purchase Order when scanning product."""
        kkr_rec = self.browse(kkr_id)
        purchase_rec = self.env["purchase.order"].browse(purchase_id)

        pol_obj = self.env["purchase.order.line"]

        # Search existing line for same product
        existing_line = purchase_rec.order_line.filtered(
            lambda l: l.product_id == kkr_rec.product_id
        )[:1]

        if existing_line:
            # Update quantity
            existing_line.product_qty += float(kkr_rec.reorder_qty)
        else:
            # Create new line
            po_line = pol_obj.new({
                "product_id": kkr_rec.product_id.id,
                "order_id": purchase_rec.id,
            })

            po_line.onchange_product_id()

            vals = pol_obj._convert_to_write({
                name: po_line[name] for name in po_line._cache
            })

            vals.update({
                "product_qty": kkr_rec.reorder_qty,
                "price_unit": kkr_rec.pricelist_id.price,
            })

            pol_obj.create(vals)

        if kkr_rec.automatic_confirm and purchase_rec.state in ["draft", "sent"]:
            purchase_rec.button_confirm()

        return True

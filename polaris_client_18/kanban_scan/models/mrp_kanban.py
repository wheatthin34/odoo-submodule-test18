# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, models, fields
import datetime


class MrpKanbanReordering(models.Model):
    _inherit = "mrp.kanban.reordering"


    @api.model
    def match_barcode_generic(self, barcode):
        """
        Match a barcode against multiple models: kanban.reordering, current model (assumed kfm), and stock.picking.

        This method aggregates barcode match results from:
            - Kanban Reordering (`kanban.reordering`)
            - KFM (assumed to be the current model)
            - Stock Receipt (`stock.picking`)

        Args:
            barcode (str): The barcode to match against.

        Returns:
            dict | bool: A dictionary with match results per model if any match is found,
                 otherwise False.
                 Example:
                 {
                     "krr": {...} or False,
                     "kfm": {...} or False,
                     "receipt": {...} or False,
                 }
        """
        krr_data = self.env["kanban.reordering"].match_barcode(barcode)

        kfm_data = self.match_barcode(barcode)

        receipt_data = self.env["stock.picking"].match_barcode(barcode)

        if not any([krr_data, kfm_data, receipt_data]):
            return False

        return {
            "krr": krr_data,
            "kfm": kfm_data, 
            "receipt": receipt_data,
        }

    @api.model
    def match_barcode(self, barcode):
        """
        Matches a given barcode with a reordering record and returns structured information based on the reordering type.

        Parameters:
            barcode (str): The barcode string to search for in reordering records.

        Returns:
            dict: A dictionary (`kfm_dict`) containing detailed data about the matched reordering record.
                  The content of the dictionary varies depending on the reordering type, which can be one of the following:
                    - internal_transfer: Includes related stock picking and move lines.
                    - inter_warehouse: Includes linked delivery and receipt stock pickings, along with their statuses.
                    - manufacturing_order: Includes MRP production orders and raw material moves.
                    - physical: Basic details only (no additional data).

            bool: Returns False if no reordering record is found for the given barcode.

        Notes:
            - The method uses internal company configurations and related stock or manufacturing models to gather data.
            - MRP or stock records linked to the same origin (reordering name) are updated or referenced.
            - The `mrp_list` in the response includes move lines, manufacturing details, or delivery information depending on context.
            - Scheduled dates are formatted to 'MM/DD/YYYY' in the response for consistency.
        """
        reordering_rec = self.search([("barcode", "=", barcode)])
        if reordering_rec:
            kfm_dict = {
                "kfm_id": reordering_rec.id,
                "name": reordering_rec.name,
                "product": reordering_rec.product_id.name,
                "quantity": reordering_rec.reorder_quantity,
                "type": {
                    "internal_transfer": "Internal Transfer",
                    "inter_warehouse": "Inter-Warehouse",
                    "manufacturing_order": "Manufacturing Order",
                    "physical": "Physical",
                }[reordering_rec.type],
                "source_location": reordering_rec.source_location.display_name or "-",
                "destination_location": reordering_rec.destination_location.display_name
                or "-",
                "minimum_quantity": reordering_rec.minimum_quantity,
            }
            mrp_list = []
            # Type = Internal Transfer
            if reordering_rec.type == "internal_transfer":
                warehouse_id = reordering_rec.source_location.warehouse_id
                con_ids = warehouse_id.internal_transfer_kanban_id
                stock_picking_id = self.env["stock.picking"].search(
                    [
                        ("state", "not in", ["cancel"]),
                        ("origin", "=", reordering_rec.name),
                    ],
                    order="id desc",
                    limit=1,
                )
                if stock_picking_id:
                    kfm_dict.update(
                        {
                            "current_stock_picking_rec_id": stock_picking_id.id,
                            "current_stock_picking_rec_name": stock_picking_id.name,
                        }
                    )
                rfq_rec = self.env["stock.picking"].search(
                    [
                        ("state", "not in", ["cancel"]),
                        ("picking_type_id", "=", con_ids.id),
                    ],
                    order="id desc",
                )
                if rfq_rec:
                    rfq_line_recs = rfq_rec.mapped("move_ids").filtered(
                        lambda t: t.product_id.id == reordering_rec.product_id.id
                    )
                    kfm_dict.update(
                        {
                            "internal_transfer_id": rfq_rec[0].id,
                            "schedule_date": datetime.datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                        }
                    )
                    STATE_LABELS = {
                        'draft': 'Draft',
                        'waiting': 'Waiting Another Operation',
                        'confirmed': 'Waiting',
                        'assigned': 'Ready',
                        'done': 'Done',
                        'cancel': 'Cancelled',
                    }
                    for rfq_line_rec in rfq_line_recs:
                        mrp_list.append(
                            {
                                "internal_transfer_id": rfq_line_rec.picking_id.id,
                                "mrp_number": rfq_line_rec.reference,
                                "source_location": rfq_line_rec.location_id.display_name,
                                "destination_location": rfq_line_rec.location_dest_id.display_name,
                                "qty": rfq_line_rec.product_uom_qty,
                                "delivery_status": STATE_LABELS.get(rfq_line_rec.picking_id.state, rfq_line_rec.picking_id.state),
                                "delivery_scheduled_date": rfq_line_rec.picking_id.scheduled_date.strftime("%m/%d/%Y") if rfq_line_rec.picking_id.scheduled_date else "",
                            }
                        )
                    kfm_dict.update({"mrp_list": mrp_list})
            # Type = Inter Warehouse
            if reordering_rec.type == "inter_warehouse":
                route_id = reordering_rec.routes_id  # Use routes_id from the reordering record
                # --- STOCK PICKINGS ---
                # Get the picking_type from stock.rule with lowest sequence for this route
                picking_type_rec = self.env['stock.rule'].search(
                    [('route_id', '=', route_id.id)], order='sequence asc', limit=1
                ).picking_type_id

                if picking_type_rec:
                    # Fetch all active stock pickings for this picking_type and product
                    stock_pickings = self.env['stock.picking'].search([
                        ('state', 'not in', ['done', 'cancel']),
                        ('picking_type_id', '=', picking_type_rec.id),
                        ('move_ids.product_id', '=', reordering_rec.product_id.id),
                    ], order='id desc')

                    for picking in stock_pickings:
                        # Compute picking_status similar to previous logic
                        receipt_state = []
                        for move in picking.move_ids:
                            receipt_state.extend([r.state for r in move.stock_picking_ids])

                        if picking.state == "done":
                            if all([x == "confirmed" for x in receipt_state]):
                                picking_status = "In Transit"
                            elif all([x == "done" for x in receipt_state]):
                                picking_status = "Done"
                            elif all([x in ["done", "confirmed"] for x in receipt_state]):
                                picking_status = "In Transit"
                            elif any([x in ["draft", "waiting", "confirmed", "assigned", "done"] for x in receipt_state]):
                                picking_status = "Partially Transit"
                        else:
                            if picking.state in ["waiting", "draft", "confirmed"]:
                                picking_status = "Created"
                            elif picking.state == "assigned":
                                picking_status = "Reserved"
                            else:
                                picking_status = picking.state

                        # Filter moves for current product
                        move_lines = picking.move_ids.filtered(lambda m: m.product_id.id == reordering_rec.product_id.id)
                        for move_line in move_lines:
                            mrp_list.append({
                                "delivery_transfer_id": move_line.picking_id.id,
                                "delivery_status": picking_status,
                                "delivery_scheduled_date": move_line.picking_id.scheduled_date.strftime("%m/%d/%Y") if move_line.picking_id.scheduled_date else "",
                                "mrp_number": move_line.reference,
                                "source_location": move_line.location_id.display_name,
                                "destination_location": move_line.location_dest_id.display_name,
                                "qty": move_line.product_uom_qty,
                            })

                kfm_dict.update({"mrp_list": mrp_list})
            # Type = Manufacturing Order
            if reordering_rec.type == "manufacturing_order":
                product_rec = reordering_rec.product_id
                mrp_production_rec = self.env["mrp.production"].search(
                    [
                        ("product_id", "=", product_rec.id),
                        ("state", "not in", ["done", "cancel"]),
                        ("origin", "=", reordering_rec.name),
                    ],
                    order="id desc",
                    limit=1,
                )
                if mrp_production_rec:
                    kfm_dict.update(
                        {
                            "current_mrp_production_rec": mrp_production_rec.name,
                            "current_mrp_production_rec_id": mrp_production_rec.id,
                        }
                    )
                mrp_production_recs = self.env["mrp.production"].search(
                    [
                        ("product_id", "=", product_rec.id),
                        ("state", "not in", ["done", "cancel"]),
                        ("origin", "=", reordering_rec.name),
                    ],
                    order="id desc",
                )
                for production_rec in mrp_production_recs:
                    production_rec.update(
                        {"product_qty": reordering_rec.reorder_quantity}
                    )
                    moves = production_rec.move_raw_ids
                    for move in moves:
                        move.update(
                            {
                                "product_uom_qty": production_rec.product_qty
                                * move.product_uom_qty
                            }
                        )
                    mrp_list.append(
                        {
                            "manuf_id": production_rec.id,
                            "mrp_number": production_rec.name,
                            "source_location": production_rec.location_src_id.display_name
                            or "-",
                            "destination_location": production_rec.location_dest_id.display_name
                            or "-",
                            "qty": production_rec.product_qty,
                            "delivery_status": production_rec.state,
                            "delivery_scheduled_date": production_rec.date_start.strftime("%m/%d/%Y") if production_rec.date_start else "",
                        }
                    )
                kfm_dict.update({"mrp_list": mrp_list})
            # Type = Physical
            if reordering_rec.type == "physical":
                return kfm_dict
            return kfm_dict
        return False

    @api.model
    def confirm_kfm_data(self, kfm_id):
        """
        Confirm the scanned KFM (Kanban Flow Management) record and take the appropriate
        action based on the operation type.

        This method handles the following types:
            - physical: Returns a flag for physical operation.
            - manufacturing_order: Creates a manufacturing order if needed, along with BoM.
            - internal_transfer: Creates or appends to internal stock pickings.
            - inter_warehouse: Manages inter-warehouse logistics by creating a delivery
              and receipt with transit locations.

        :param int kfm_id: ID of the KFM record to confirm.
        :return: A dictionary containing flags and references based on the type of operation.
        """
        kfm_rec = self.browse(kfm_id)
        # Type = Physical
        if kfm_rec.type == "physical":
            return {"physical": True}

        # Type = Manufacturing Order
        if kfm_rec.type == "manufacturing_order":
            bom = self.env["mrp.bom"]
            product_rec = kfm_rec.product_id
            product_tmpl_rec = product_rec.product_tmpl_id
            bom_rec = bom.search(
                [("product_tmpl_id", "=", product_tmpl_rec.id)], limit=1
            )
            if not bom_rec:
                bom_rec = bom.create(
                    {
                        "product_tmpl_id": product_tmpl_rec.id,
                        "product_qty": 1,
                        "type": "normal",
                        "ready_to_produce": "asap",
                    }
                )
                self.env["mrp.bom.line"].create(
                    {
                        "product_id": product_rec.id,
                        "product_qty": 1,
                        "bom_id": bom_rec.id,
                    }
                )

            mrp_production = self.env["mrp.production"].new(
                {
                    "product_id": product_rec.id,
                    "product_qty": kfm_rec.reorder_quantity,
                    "bom_id": bom_rec.id,
                    "date_start": str(
                        datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                    ),
                    "user_id": self.env.user.id,
                    "product_uom_id": product_rec.uom_id.id,
                    "origin": kfm_rec.name,
                    "company_id": bom_rec.company_id.id,
                }
            )
            mrp = mrp_production._convert_to_write(
                {name: mrp_production[name] for name in mrp_production._cache}
            )
            mrp_production_rec = self.env["mrp.production"].create(mrp)
            moves = mrp_production_rec.move_raw_ids
            for move in moves:
                move.update(
                    {
                        "product_uom_qty": mrp_production_rec.product_qty
                        * move.product_uom_qty
                    }
                )
            return {
                "manufacturing_order": True,
                "manufacturing_order_id": mrp_production_rec.id,
                "manufacturing_order_name": mrp_production_rec.name,
            }

        # Type = Internal Transfer
        if kfm_rec.type == "internal_transfer":
            warehouse_id = kfm_rec.source_location.warehouse_id
            con_ids = warehouse_id.internal_transfer_kanban_id
            if con_ids:
                stock_picking_id = self.env["stock.picking"].search(
                    [
                        ("state", "not in", ["done", "cancel"]),
                        ("picking_type_id", "=", con_ids.id),
                        ("location_id", "=", kfm_rec.source_location.id),
                        ("location_dest_id", "=", kfm_rec.destination_location.id),
                    ],
                    order="id desc",
                    limit=1,
                )
                # if create separate transfer boolean is not checked that add
                # this line in existing transfer whose matches its source &
                # destination location
                if not kfm_rec.create_transfer_scan and stock_picking_id:
                    move_line_obj = self.env["stock.move"]
                    move_line_data = {
                        "picking_id": stock_picking_id.id,
                        "product_id": kfm_rec.product_id.id,
                        "product_uom_qty": kfm_rec.reorder_quantity,
                        "name": kfm_rec.name,
                        "location_id": kfm_rec.source_location.id,
                        "location_dest_id": kfm_rec.destination_location.id,
                    }
                    if not stock_picking_id.origin:
                        stock_picking_id.update({"origin": kfm_rec.name})
                    move_line_obj.create(move_line_data)
                    stock_picking_id._autoconfirm_picking()
                    exsit_list = []
                    if stock_picking_id.origin:
                        exsit_list = [
                            True
                            for origin in stock_picking_id.origin.split(",")
                            if origin == kfm_rec.name
                        ]
                    if not exsit_list:
                        stock_picking_id.origin = (
                            stock_picking_id.origin + "," + kfm_rec.name
                        )
                # if create separate transfer boolean is checked then create
                # separate transfer for this
                if kfm_rec.create_transfer_scan or not stock_picking_id:
                    # Create picking with waiting stage
                    stock_picking_id = self.env["stock.picking"].create(
                        {
                            "origin": kfm_rec.name,
                            "picking_type_id": con_ids.id,
                            "location_id": kfm_rec.source_location.id,
                            "location_dest_id": kfm_rec.destination_location.id,
                            "move_ids": [
                                (
                                    0,
                                    0,
                                    {
                                        "product_id": kfm_rec.product_id.id,
                                        "product_uom_qty": kfm_rec.reorder_quantity,
                                        "name": kfm_rec.name,
                                        "location_id": kfm_rec.source_location.id,
                                        "location_dest_id": kfm_rec.destination_location.id,
                                    },
                                )
                            ],
                        }
                    )
                if stock_picking_id and kfm_rec.validate_transfer_on_scan:
                    stock_picking_id.with_context({"system_validation": True}).button_validate()
                else:
                    stock_picking_id.action_confirm()
            else:
                return {"internal_transfer": False}
            return {
                "internal_transfer": True,
                "internal_picking_id": stock_picking_id.id,
                "internal_picking_name": stock_picking_id.name,
            }

        # Type = Inter Warehouse
        if kfm_rec.type == "inter_warehouse":
            procurements = []
            values = {
                    'route_ids': kfm_rec.routes_id,
                    'date_planned': fields.Datetime.now(),
                    'date_order': fields.Datetime.now(),
                    'date_deadline': fields.Datetime.now(),
                    'warehouse_id': kfm_rec.destination_location.warehouse_id,
                    'company_id': kfm_rec.destination_location.company_id
            }
            procurements.append(self.env['procurement.group'].Procurement(
                kfm_rec.product_id, kfm_rec.reorder_quantity,
                kfm_rec.product_id.uom_id, kfm_rec.destination_location,
                kfm_rec.name, kfm_rec.name, kfm_rec.destination_location.company_id,
                values))
            self.env['procurement.group'].run(procurements)

            created_pickings = self.env['stock.picking'].search([
                ('move_ids.origin', '=', kfm_rec.name),
            ], order = 'create_date desc')

            purchase = self.env['purchase.order'].search([
                ('origin', 'ilike', kfm_rec.name),
                ('state', '=', 'draft'),
                ('create_date', '>=', fields.Datetime.now())
            ], limit=1, order = 'create_date desc')

            pick = created_pickings.filtered(
                lambda p: p.picking_type_id.code == 'internal' \
                    and 'pick' in p.picking_type_id.name.lower())[:1]
            pick_next_pickings = pick.move_ids.move_dest_ids.picking_id
            pick_next_pickings.filtered(lambda p: p not in pick.return_ids)

            delivery = pick_next_pickings if pick_next_pickings else created_pickings.filtered(
                lambda p: p.picking_type_id.code == 'outgoing')[:1]
            delivery_next_pickings = delivery.move_ids.move_dest_ids.picking_id
            delivery_next_pickings.filtered(lambda p: p not in delivery.return_ids)

            receipt = delivery_next_pickings if delivery_next_pickings else created_pickings.filtered(
                lambda p: p.picking_type_id.code == 'incoming')[:1]
            receipt_next_pickings = receipt.move_ids.move_dest_ids.picking_id
            receipt_next_pickings.filtered(lambda p: p not in receipt.return_ids)

            putaway = receipt_next_pickings if receipt_next_pickings else created_pickings.filtered(
                lambda p: p.picking_type_id.code == 'internal' \
                    and 'putaway' in p.picking_type_id.name.lower())[:1]

            if pick:
                pick.origin = kfm_rec.name
                pick.action_confirm()

            if delivery:
                delivery.origin = kfm_rec.name
                delivery.action_confirm()

            if receipt:
                receipt.origin = kfm_rec.name
                receipt.action_confirm()

            if putaway:
                putaway.origin = kfm_rec.name
                putaway.action_confirm()

            return {
                "inter_warehouse": True,
                "pick_order_id": pick.id if pick else False,
                "pick_order_name": pick.picking_type_id.display_name + ": " + pick.name if pick else "",
                "delivery_order_id": delivery.id if delivery else False,
                "delivery_order_name": delivery.name if delivery else "",
                "receipt_id": receipt.id if receipt else False,
                "receipt_name": receipt.picking_type_id.display_name + ": " + receipt.name if receipt else "",
                "putaway_id": putaway.id if putaway else False,
                "putaway_name": putaway.picking_type_id.display_name + ": " + putaway.name if putaway else "",
                "purchase_id": purchase.id if purchase else False,
                "purchase_name": purchase.name if purchase else "",
            }

    @api.model
    def open_picking(self):
        """Function call for open picking from screen."""
        pass

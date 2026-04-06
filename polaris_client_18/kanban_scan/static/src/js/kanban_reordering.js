/** @odoo-module **/
import { Component, useRef, onMounted, useState } from "@odoo/owl";
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

export class MrpReorderingKanbanScan extends Component {
    setup() {
        this.orm = useService('orm');
        this.action = useService('action');
        this.barcodeField = useRef("barcodeField");
        this.dialogService = useService("dialog");

        // Set initial state
        this.state = useState({
            showScankioskMode: false,
            showBarcodeUnmatched: false,
            showBarcodeMatchedKFM: false,
            showBarcodeMatchedKRR: false,
            showBarcodeReceipt: false,
            showRFQCreated: false,
            showReceiptVal: false,
            showRFQUpdated: false,
            showNotInternalTransfer: false,
            showLocationError: false,
            showMrpCreatedData: false,
            showMrpID: false,
            showInternalTransferId: false,
            showDeliveryOrderId: false,
            showpickOrderId: false,
            showReceiptId: false,
            showPutawayId: false,
            showPurchaseId: false,
            showScheduleDate: false,
            showDeliveryState: false,
            showReceiptNotValidate: false,
            krrData: {
                name: '',
                product: '',
                vendor: '',
                quantity: '',
                purchaseList: [],
            },
            kfmData: {
                name: '',
                type: '',
                source_location: '',
                destination_location: '',
                schedule_date: '',
                product: '',
                mrpList: [],
            },
            receiptData: {
                receiptSource: '',
                receiptList: [],
            },
            mrpOrderId: '',
            mrpOrderName: '',
            internalTransferId: '',
            internalTransferName: '',
            pickOrderId: '',
            pickOrderName: '',
            deliveryOrderId: '',
            deliveryOrderName: '',
            receiptId: '',
            receiptName: '',
            putawayId: '',
            putawayName: '',
            purchaseId: '',
            purchaseName: '',
        });

        onMounted(() => {
            this.focusBarcodeField();
        });

        // Handle input event for the barcode
        this.onBarcodeInput = (ev) => {

            // Hide the error message on new input
            this.state.showBarcodeUnmatched = false;
            this.state.showBarcodeMatchedKFM = false;
            this.state.showBarcodeMatchedKRR = false;
            this.state.showBarcodeReceipt = false;
            this.state.showRFQUpdated = false;
            this.state.showRFQCreated = false;
            this.state.showMrpCreatedData = false;
            this.state.showReceiptNotValidate = false;
            this.state.showReceiptNotValidate = false;
            this.state.showReceiptVal = false;
        };

        // Bind open_list_record method
        this.openListRecord = this.openListRecord.bind(this);
    }

    focusBarcodeField() {
        const tryFocus = () => {
            if (this.barcodeField && this.barcodeField.el) {
                this.barcodeField.el.focus();
            } else {
                setTimeout(tryFocus, 100); // Retry after 100ms
            }
        };
        tryFocus(); 
    }

    async scanBarcode(ev) {
        const barcode = this.barcodeField.el.value;
        const matchData = await this.orm.call("mrp.kanban.reordering", "match_barcode_generic", [barcode]);
        this.processMatchData(matchData);
    }

    processMatchData(matchData) {
        // Raise warning if Data not matched.
        if (!matchData) {
            this.focusBarcodeField();
            this.state.showBarcodeUnmatched = true;
        } else if (matchData.kfm.create_picking == true) {
            this.state.showRFQCreated = true;
            this.focusBarcodeField();
        } else if (matchData.kfm.error == 'location_error') {
            this.state.showLocationError = true;
            this.focusBarcodeField();
        } else {
            if (matchData.krr) {

                // Show output if Kanban Reordering Data matched.
                this.state.showBarcodeMatchedKRR = true;
                this.state.showScankioskMode = true;

                // Clear the purchaseList before populating with new data
                this.state.krrData.purchaseList.splice(0, this.state.krrData.purchaseList.length);

                // Update KRR Details         
                this.state.krrData = {
                    name: matchData.krr.name,
                    product: matchData.krr.product,
                    vendor: matchData.krr.vendor,
                    quantity: matchData.krr.quantity,
                    purchaseList: matchData.krr.purchase_list
                }
                // Update Purchase Details
                this.kkrId = matchData.krr.kkr_id;
                this.purchaseExist = matchData.krr.purchase_exist;
                this.purchaseId = matchData.krr.purchase_id;
                this.purchaseNumber = matchData.krr.current_purchase_order_rec_name;

            }
            if (matchData.kfm) {

                // Show output if KFM Data matched.
                this.state.showBarcodeMatchedKFM = true;
                this.state.showScankioskMode = true;

                //Update MRP data
                this.currentStockId = matchData.kfm.current_stock_picking_rec_id;
                this.receiptStockId = matchData.kfm.stock_picking_receipt_id;
                this.currentMrpId = matchData.kfm.current_mrp_production_rec_id;
                this.kfmId = matchData.kfm.kfm_id;

                // Clear the mrpList before populating with new data
                this.state.kfmData.mrpList.splice(0, this.state.kfmData.mrpList.length);

                // Update KFM data
                this.state.kfmData = {
                    name: matchData.kfm.name,
                    type: matchData.kfm.type,
                    source_location: matchData.kfm.source_location,
                    destination_location: matchData.kfm.destination_location,
                    schedule_date: matchData.kfm.schedule_date,
                    product: matchData.kfm.product,
                    mrpList: this.prepareMrpList(matchData.kfm.mrp_list)
                }
            }
            if (matchData.receipt) {
                // Show output if Receipt Data matched.
                this.state.showBarcodeReceipt = true;
                this.state.showScankioskMode = true;


                // Clear the receipt list before populating with new data
                this.state.receiptData.receiptList.splice(0, this.state.receiptData.receiptList.length);

                //Update Receipt data
                this.state.receiptData = {
                    receiptSource: matchData.receipt.source,
                    receiptList: matchData.receipt.receipt_list,
                }
                this.receiptRecordId = matchData.receipt.receipt_record_id;
            }
        }
    }

    prepareMrpList(mrpList) {

        if (Array.isArray(mrpList)) {
            return mrpList.map((mrpData) => {
                let result = {
                    id: null,
                    mrp_number: mrpData.mrp_number,
                    source_location: mrpData.source_location || '',
                    destination_location: mrpData.destination_location || '',
                    qty: mrpData.qty || 0,
                    delivery_scheduled_date: mrpData.delivery_scheduled_date || '',
                    delivery_status: mrpData.delivery_status || '',
                };
                if (mrpData.manuf_id) {
                    result.id = mrpData.manuf_id;
                } else if (mrpData.internal_transfer_id) {
                    result.id = mrpData.internal_transfer_id;
                } else if (mrpData.delivery_transfer_id) {
                    result.id = mrpData.delivery_transfer_id;
                    this.state.showScheduleDate = true;
                    this.state.showDeliveryState = true;
                }
                return result;
            });
        } else { return []; }
    }

    async confirmKFM() {
        const mrpData = await this.orm.call("mrp.kanban.reordering", "confirm_kfm_data", [this.kfmId]);
        if (mrpData) {
            if (mrpData.manufacturing_order == true) {
                this.state.mrpOrderId = mrpData.manufacturing_order_id;
                this.state.mrpOrderName = mrpData.manufacturing_order_name;
                this.state.showMrpCreatedData = true;
                this.state.showBarcodeMatchedKFM = false;
                this.state.showMrpID = true;
                this.state.showScankioskMode = false;
                this.focusBarcodeField();
            } else if (mrpData.internal_transfer == false) {
                this.state.showNotInternalTransfer = true;
                this.state.showMrpCreatedData = true;
                this.state.showBarcodeMatchedKFM = false;
                this.state.showScankioskMode = false;
                this.focusBarcodeField();
            } else if (mrpData.internal_transfer == true) {
                this.state.internalTransferId = mrpData.internal_picking_id;
                this.state.internalTransferName = mrpData.internal_picking_name;
                this.state.showInternalTransferId = true;
                this.state.showMrpCreatedData = true;
                this.state.showBarcodeMatchedKFM = false;
                this.state.showScankioskMode = false;
                this.focusBarcodeField();
            } else if (mrpData.inter_warehouse == true) {
                this.state.pickOrderId = mrpData.pick_order_id;
                this.state.pickOrderName = mrpData.pick_order_name;
                this.state.deliveryOrderId = mrpData.delivery_order_id;
                this.state.deliveryOrderName = mrpData.delivery_order_name;
                this.state.receiptId = mrpData.receipt_id;
                this.state.receiptName = mrpData.receipt_name;
                this.state.putawayId = mrpData.putaway_id;
                this.state.putawayName = mrpData.putaway_name;
                this.state.purchaseId = mrpData.purchase_id;
                this.state.purchaseName = mrpData.purchase_name;
                this.state.showMrpCreatedData = true;
                this.state.showDeliveryOrderId = true;
                this.state.showpickOrderId = true;
                this.state.showPurchaseId = mrpData.purchase_id ? true : false;
                this.state.showReceiptId = mrpData.receipt_id ? true : false;
                this.state.showPutawayId = mrpData.putaway_id ? true : false;
                this.state.showBarcodeMatchedKFM = false;
                this.state.showScankioskMode = false;
                this.focusBarcodeField();
            } else if (mrpData.physical == true) {
                this.state.showBarcodeMatchedKFM = false;
                this.state.showScankioskMode = false;
                this.focusBarcodeField();
            }
        }
    }

    async confirmKRR() {
        if (this.purchaseExist == true) {
            await this.orm.call("kanban.reordering", "update_po", [this.purchaseId, this.kkrId]);
            this.state.updatePurchaseId = this.purchaseNumber;
            this.state.showRFQUpdated = true;
            this.state.showBarcodeMatchedKRR = false;
            this.state.showScankioskMode = false;
            this.focusBarcodeField();
        } else {
            const createdPurchaseData = await this.orm.call("kanban.reordering", "create_po", [this.kkrId])
            this.state.createPurchaseId = createdPurchaseData[1];
            this.createPurchaseId = createdPurchaseData[0];
            this.state.showRFQCreated = true;
            this.state.showBarcodeMatchedKRR = false;
            this.state.showScankioskMode = false;
            this.focusBarcodeField();
        }
    }

    async confirmReceipt() {
        this.dialogService.add(ConfirmationDialog, {
            body: _t("Do you really want to confirm Receipt?"),
            confirm: async () => {
                const receiptData = await this.orm.call('stock.picking', 'confirm_receipt_data', [this.receiptRecordId]);
                if (receiptData) {
                    if (receiptData.receipt_value == false) {
                        this.state.showBarcodeReceipt = false;
                        this.state.showScankioskMode = false;
                        this.state.showReceiptNotValidate = true;
                        this.focusBarcodeField();
                    } else {
                        this.state.showBarcodeReceipt = false;
                        this.state.showReceiptVal = true;
                        this.state.stockReceipt = receiptData.stock_receipt;
                        this.state.stockReceiptName = receiptData.stock_receipt_name;
                        this.state.showScankioskMode = false;
                        this.focusBarcodeField();
                    }
                }
            }
        });
    }

    openPurchaseOrder() {
        if (this.purchaseId) {
            this.action.doAction({
                name: 'Requests for Quotation',
                res_model: 'purchase.order',
                views: [
                    [false, 'form']
                ],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(this.purchaseId),
                target: 'current',
            });
        } else {
            this.action.doAction({
                name: 'Requests for Quotation',
                res_model: 'purchase.order',
                views: [
                    [false, 'form']
                ],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(this.createPurchaseId),
                target: 'current',
            });
        }
    }

    openStockReceipt() {
        if (this.receiptRecordId) {
            this.action.doAction({
                name: 'Stock Operations',
                res_model: 'stock.picking',
                views: [
                    [false, 'form']
                ],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(this.receiptRecordId),
                target: 'current',
            });
        }
    }

    async openReceiptData(ev) {
        const receipt = await this.state.receiptId;
        if (receipt) {
            this.action.doAction({
                name: 'Stock Operations',
                res_model: 'stock.picking',
                views: [
                    [false, 'form']
                ],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(receipt),
                target: 'current',
            });
        }
    }

    async openDeliveryOrder(ev) {
        const deliveryOrder = await this.state.deliveryOrderId;
        if (deliveryOrder) {
            this.action.doAction({
                name: 'Stock Operations',
                res_model: 'stock.picking',
                views: [
                    [false, 'form']
                ],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(deliveryOrder),
                target: 'current',
            });
        }
    }

    async openPutawayOrder(ev) {
        const putwayOrder = await this.state.putawayId;
        if (putwayOrder) {
            this.action.doAction({
                name: 'Stock Operations',
                res_model: 'stock.picking',
                views: [
                    [false, 'form']
                ],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(putwayOrder),
                target: 'current',
            });
        }
    }

    async openpickOrder(ev) {
        const pickOrder = await this.state.pickOrderId;
        if (pickOrder) {
            this.action.doAction({
                name: 'Stock Operations',
                res_model: 'stock.picking',
                views: [
                    [false, 'form']
                ],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(pickOrder),
                target: 'current',
            });
        }
    }

    async openInternalTransfer(ev) {
        const internalTransfer = await this.state.internalTransferId;
        if (internalTransfer) {
            this.action.doAction({
                name: 'Stock Operations',
                res_model: 'stock.picking',
                views: [
                    [false, 'form']
                ],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(internalTransfer),
                target: 'current',
            });
        }
    }

    async openManufacturingData(ev) {
        const mrpId = await this.state.mrpOrderId;
        if (mrpId) {
            this.action.doAction({
                name: 'MRP Production',
                res_model: 'mrp.production',
                views: [
                    [false, 'form']
                ],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(mrpId),
                target: 'current',
            });
        }
    }

    async pickingButton() {
        await this.orm.call("mrp.kanban.reordering", "open_picking", []);
    }

    openListRecord(ev) {
        const recordId = ev.target.dataset.id;
        if (this.purchaseId) {
            this.action.doAction({
                name: 'Requests for Quotation',
                res_model: 'purchase.order',
                views: [
                    [false, 'form']
                ],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(recordId),
                target: 'current',
            });
        } else if (this.currentMrpId) {
            this.action.doAction({
                name: 'MRP Production',
                res_model: 'mrp.production',
                views: [
                    [false, 'form']
                ],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(recordId),
                target: 'current',
            });
        } else if (this.currentStockId) {
            this.action.doAction({
                name: 'Stock Operations',
                res_model: 'stock.picking',
                views: [
                    [false, 'form']
                ],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(recordId),
                target: 'current',
            });
        } else if (this.receiptStockId) {
            this.action.doAction({
                name: 'Stock Operations',
                res_model: 'stock.picking',
                views: [
                    [false, 'form']
                ],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(recordId),
                target: 'current',
            });
        } else if (this.receiptRecordId) {
            this.action.doAction({
                name: 'Stock Receipt',
                res_model: 'stock.picking',
                views: [
                    [false, 'form']
                ],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(recordId),
                target: 'current',
            });
        }
    }

    async openPurchaseData(ev) {
        const purchase = await this.state.purchaseId;
        if (purchase) {
            this.action.doAction({
                name: 'Requests for Quotation',
                res_model: 'purchase.order',
                views: [
                    [false, 'form']
                ],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(purchase),
                target: 'current',
            });
        }
    }

    cancelScan() {
        this.state.showScankioskMode = false;
        this.state.showBarcodeMatchedKRR = false;
        this.state.showBarcodeMatchedKFM = false;
        this.state.showBarcodeReceipt = false;
        this.state.showRFQUpdated = false;
        this.state.showRFQCreated = false;
        this.focusBarcodeField();
    }
}
MrpReorderingKanbanScan.template = 'kanban_scan.MrpReorderingKanban';
registry.category('actions').add('mrp_reordering_kanban', MrpReorderingKanbanScan);
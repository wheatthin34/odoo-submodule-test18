# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

{
    "name": "Kanban For Manufacturing",
    "summary": """Kanban For Manufacturing""",
    "description": """Kanban For Manufacturing""",
    "author": "S4 Solutions, LLC",
    "website": "https://www.sfour.io/",
    "category": "MRP",
    "version": "18.0.0.3.0",
    "license": "OPL-1",
    "depends": [
        "mrp",
        "stock",
        "purchase",
        "polaris_manage_api_key"
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence_data.xml",
        "data/data.xml",
        "data/res_groups.xml",
        "views/mrp_kanban_view.xml",
        "views/company_view.xml",
        "views/product_template_views.xml",
        "views/stock_picking_views.xml",
        "views/stock_picking_type_views.xml",
        "views/kanban_reordering.xml",
        "views/menu.xml",
        "report/product_label_report.xml",
        "report/product_label_template.xml",
        "report/report_kfm_barcode.xml",
        "report/report_krr_barcode.xml",
        "report/report_views.xml",
        "report/delivery_slip_report.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'kanban_for_manufacturing/static/src/js/locked_menu.js',
        ],
    },
    "application": True,
    "installable": True,
    "auto_install": False,
}

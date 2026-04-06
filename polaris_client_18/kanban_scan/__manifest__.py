# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

{
    "name": "Kanban Scan",
    "summary": """Kanban Scan""",
    "description": """Kanban Scan""",
    "author": "S4 Solutions, LLC",
    "website": "https://www.sfour.io/",
    "category": "MRP",
    "version": "18.0.1.4.0",
    "license": "OPL-1",
    "depends": [
        "kanban_for_manufacturing"
    ],
    "data": [
        "views/kanban_menu.xml",
        "views/stock_warehouse_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "kanban_scan/static/src/js/kanban_reordering.js",
            "kanban_scan/static/src/xml/kanban_reordering.xml",
            "kanban_scan/static/src/scss/kfm_krr_barcode.scss",
        ],
    },
    "application": True,
    "installable": True,
    "auto_install": False,
}

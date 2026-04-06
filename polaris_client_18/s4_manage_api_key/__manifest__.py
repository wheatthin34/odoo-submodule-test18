# -*- coding: utf-8 -*-
# © 2024-Today Polaris Integrators (https://polarisintegrators.com/).
# See LICENSE file for full copyright & licensing details.

{
    "name": "S4 Manage API key",
    "summary": """S4 Manage API key""",
    "description": """S4 Manage API key""",
    "author": "S4 Integrators",
    "website": "https://www.sfour.io/",
    "category": "Uncategorized",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "base",
        "base_setup",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/manage_module_api_key_views.xml",
    ],
    "application": True,
    "auto_install": False,
}

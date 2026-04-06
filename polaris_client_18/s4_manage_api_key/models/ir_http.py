# -*- coding: utf-8 -*-
from odoo import models


class Http(models.AbstractModel):
    _inherit = "ir.http"

    def connect_to_odoo_server_polaris_custom_module_code(self, api_key=None):
        return

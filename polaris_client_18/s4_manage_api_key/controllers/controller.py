# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError


class SfourAPIController(http.Controller):


    @http.route("/api_validation", type="json", auth="public")
    def api_validation(self, **kw):
        # TODO: need to copy this file for another module
        """This method is used to validate api key, this method called from tree view and schedule action.
        Note: If you will copy this file for another module, so make sure change the module name and group name
        """
        data = json.loads(http.request.httprequest.data)
        api_key_ids = (
            request.env["manage.module.api.key"]
            .sudo()
            .search(
                [
                    ("api_key", "=", data["api_key"]),
                    ("name", "=", data["technical_name"]),
                ]
            )
        )
        for rec in api_key_ids:
            rec.sudo().validate_api_details()

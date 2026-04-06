# -*- coding: utf-8 -*-
import requests
from odoo import models


class Http(models.AbstractModel):
    _inherit = "ir.http"

    def connect_to_odoo_server_polaris_custom_module_code(
        self, api_key_id=None, check_auth_key=None
    ):
        # TODO: need to copy this file for another module
        """
        Cron job method to check for validation of api key
        Note: If you will copy this file for another module, so make sure change the module name and group name
        """
        if not api_key_id:
            return None
        if api_key_id.name != "kanban_for_manufacturing":
            return super().connect_to_odoo_server_polaris_custom_module_code(
                api_key_id=api_key_id
            )
        # TODO: below endpoint is my local environment
        common_url = "https://sfour-staging-28298148.dev.odoo.com/"  # Staging URL
        endpoint = ''
        if not check_auth_key and not self.env.context.get("renew_subscription"):
            endpoint = common_url + "/api_validation"
        elif not self.env.context.get("renew_subscription"):
            endpoint = common_url + "/validate/auth_key"
        elif self.env.context.get("renew_subscription"):
            endpoint = common_url + "/renew_subscription"

        params = self.env["ir.config_parameter"].sudo()
        payload = {
            "client_domain": params.get_param("web.base.url"),
            "api_key": api_key_id.api_key,
            "module_name": "kanban_for_manufacturing",
        }
        try:
            response = requests.post(
                endpoint,
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            try:
                response_data = response.json()
                return response_data
            except Exception as e:
                return e
        except KeyError:
            print("The 'result' key is missing in the JSON response.")
            return None

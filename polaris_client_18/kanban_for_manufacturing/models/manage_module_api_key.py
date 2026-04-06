# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64


class ManageModuleApiKey(models.Model):
    _inherit = "manage.module.api.key"

    def validate_api_details(self):
        # TODO: need to copy this file for another module
        """This method is used to validate api key, this method called from tree view and schedule action.
        Note: If you will copy this file for another module, so make sure change the module name and group name
        """
        if self._context.get("from_other_method"):
            return
        api_key_id = self
        from_cron = False
        if api_key_id and not api_key_id.api_key:
            raise ValidationError("Please add the API key!")

        if not api_key_id:
            api_key_id = self.env.ref("kanban_for_manufacturing.validate_api")
            if not api_key_id.api_key:
                return
            from_cron = True
        elif api_key_id.name != "kanban_for_manufacturing":
            return super(ManageModuleApiKey, self).validate_api_details()

        http_obj = self.env[
            "ir.http"
        ].connect_to_odoo_server_polaris_custom_module_code(api_key_id=api_key_id)
        result = http_obj.get("result")

        if result and result.get("status") in ("valid_key", "grace_key"):
            # Both valid and grace period = active (grace is invisible to the customer)
            api_key_id.write({"api_status": "active"})
            if result.get("key_expiration_date"):
                api_key_id.write({"key_expiration_date": result.get("key_expiration_date")})
            if result.get("status") == "grace_key":
                grace_period = str(result.get("grace_period"))
                api_key_id.write({"grace_period": grace_period})

            kanban_group = self.env.ref(
                "kanban_for_manufacturing.group_kanban_manufacturing_user"
            )
            kanban_group.write({"users": [(4, self.env.user.id)]})
            kanban_scan_group = self.env.ref(
                "kanban_for_manufacturing.group_kanban_scan_mo_user"
            )
            kanban_scan_group.write({"users": [(4, self.env.user.id)]})
            if not from_cron:
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "type": "success",
                        "title": "Connection Successful",
                        "message": "API Validated Successfully",
                        "sticky": False,
                        "next": {"type": "ir.actions.act_window_close"},
                    },
                }
        else:
            # Subscription fully expired
            api_key_id.write({
                "api_status": "expired",
                "key_expiration_date": False,
                "grace_period": 0,
            })
            kanban_scan_group = self.env.ref(
                "kanban_for_manufacturing.group_kanban_scan_mo_user"
            )
            kanban_scan_group.write({"users": [(5, self.env.user.id)]})
            if not from_cron:
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "type": "warning",
                        "title": "Subscription Expired",
                        "message": (
                            "Your Kanban for Manufacturing subscription has expired. "
                            "Please renew to restore access."
                        ),
                        "sticky": False,
                        "next": {"type": "ir.actions.act_window_close"},
                    },
                }

        return super().validate_api_details()

    def action_renew_subscription(self):
        # TODO: need to copy this file for another module
        """This method is used to validate api key, this method called from tree view and schedule action.
        Note: If you will copy this file for another module, so make sure change the module name and group name
        """
        if self._context.get("from_other_method"):
            return

        api_key_id = self
        from_cron = False

        if api_key_id and not api_key_id.api_key:
            raise ValidationError("Please add the API key!")

        if not api_key_id:
            api_key_id = self.env.ref("kanban_for_manufacturing.validate_api")
            if not api_key_id.api_key:
                return
            from_cron = True
        elif api_key_id.name != "kanban_for_manufacturing":
            return super().validate_api_details()

        http_obj = self.env[
            "ir.http"
        ].with_context(renew_subscription=True).connect_to_odoo_server_polaris_custom_module_code(api_key_id=api_key_id)
        result = http_obj.get("result")
        common_url = "https://sfour-staging-28298148.dev.odoo.com/"
        if result and result.get("url"):
            url = result.get("url").replace("/@/", common_url)
            return {
                "type": "ir.actions.act_url",
                "url": url,
                "target": "new",
            }
        else:
            raise ValidationError("Your API key is not valid.")

        return super().action_renew_subscription()

def connect_main_server_check_auth_key(self):
        # TODO: need to copy this file for another module
        """
        Cron job method to check for validation of api key
        we will deploy a cron job on the client side with added security measures.
        """
        api_key_id = self.env.ref("kanban_for_manufacturing.validate_api")
        if api_key_id.api_key:
            http_obj = self.env[
                "ir.http"
            ].connect_to_odoo_server_polaris_custom_module_code(
                api_key_id=api_key_id, check_auth_key=True
            )
            result = http_obj.get("result")
            if result and "auth_key" in result and not result.get("auth_key"):
                kanban_scan_group = self.env.ref(
                    "kanban_for_manufacturing.group_kanban_scan_mo_user"
                )
                kanban_scan_group.sudo().write({"users": [(5, self.env.user.id)]})
                api_key_id.sudo().with_context(from_other_method=True).write(
                    {"api_key": False}
                )
        else:
            api_key_id.sudo().write({"api_status": "expired"})
            kanban_scan_group = self.env.ref(
                "kanban_for_manufacturing.group_kanban_scan_mo_user"
            )
            kanban_scan_group.sudo().write({"users": [(5, self.env.user.id)]})

        return super().connect_main_server_check_auth_key()

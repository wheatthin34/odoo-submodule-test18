# -*- coding: utf-8 -*-
from odoo import models, fields, api
import datetime


class ManageModuleApiKey(models.Model):
    _name = "manage.module.api.key"
    _description = "Manage Module API Key"

    _sql_constraints = [
        ("name_api_key_uniq", "unique(name, api_key)", "API key must be unique !"),
    ]

    name = fields.Char(string="Technical Module Name", readonly="1")
    api_key = fields.Char(string="API Key")
    remaining_days = fields.Integer(
        string="Remaining Days", readonly="1", compute="_compute_remaining_days"
    )
    key_expiration_date = fields.Date(string="Key Expiration date")
    grace_period = fields.Char(string="Grace Period", readonly="1")
    api_status = fields.Selection(
        selection=[
            ("active", "Active"),
            ("expired", "Expired"),
        ],
        string="Status",
        default="expired",
        readonly="1"
    )

    def action_renew_subscription(self):
        return

    def validate_api_details(self):
        return

    def connect_main_server_check_auth_key(self):
        return

    def _compute_remaining_days(self):
        for rec in self:
            if (
                rec.key_expiration_date
                and rec.key_expiration_date > datetime.date.today()
            ):
                rec.remaining_days = (
                    rec.key_expiration_date - datetime.date.today()
                ).days
            else:
                rec.remaining_days = 0

    def write(self, vals):
        res = super().write(vals)
        if "api_key" in vals:
            for rec in self:
                rec.validate_api_details()
        return res

    @api.model
    def get_subscription_state_for_module(self, module_name):
        """
        Called by the JS frontend via RPC.
        Returns: { 'state': 'active' | 'expired' }
        """
        record = self.search([("name", "=", module_name)], limit=1)
        if not record:
            return {"state": "active"}
        return {"state": record.api_status or "active"}
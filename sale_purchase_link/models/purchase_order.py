# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    """
    Extend purchase.order to store a link back to the originating Sales Order
    and provide a smart-button action to open it.
    """

    _inherit = "purchase.order"

    sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sales Order",
        index=True,
        copy=False,
        help="Sales Order from which this Purchase Order was created.",
    )

    def action_view_sale_order(self):
        """
        Smart button handler: open the linked Sales Order.
        """
        self.ensure_one()
        if not self.sale_order_id:
            raise UserError(_("No Sales Order is linked to this Purchase Order."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Sales Order"),
            "res_model": "sale.order",
            "view_mode": "form",
            "res_id": self.sale_order_id.id,
            "target": "current",
        }

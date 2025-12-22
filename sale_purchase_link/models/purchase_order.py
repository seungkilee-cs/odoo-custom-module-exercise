# -*- coding: utf-8 -*-

from odoo import _, fields, models


class PurchaseOrder(models.Model):
    """
    Extend purchase.order to store its source Sales Order
    """

    _inherit = "purchase.order"

    # temp disable for the sale order side
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        help="Sales Order from which this Purchase Order was created.",
        index=True,
        copy=False,
    )

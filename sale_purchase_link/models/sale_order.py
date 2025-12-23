# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    purchase_order_ids = fields.One2many(
        comodel_name="purchase.order",
        inverse_name="sale_order_id",
        string="Purchase Orders",
        copy=False,
        help="Purchase Orders created from this Sales Order.",
    )

    purchase_order_count = fields.Integer(
        string="PO Count",
        compute="_compute_purchase_order_count",
        store=False,
        help="Number of Purchase Orders linked to this Sales Order.",
    )

    @api.depends("purchase_order_ids")
    def _compute_purchase_order_count(self):
        """Compute the number of linked purchase orders."""
        for order in self:
            order.purchase_order_count = len(order.purchase_order_ids)

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------

    def action_create_purchase_order(self):
        """
        Create a Purchase Order (RFQ) from this Sales Order.

        - If a PO already exists, open the existing PO(s) instead of creating.
        - purchase.order requires a Vendor (partner_id), so default one.
        - Link PO back to SO via purchase.order.sale_order_id.
        """
        self.ensure_one()

        # Enforce UI expectation in server-side logic
        if self.purchase_order_ids:
            return self.action_view_purchase_orders()

        if not self.order_line:
            raise UserError(
                _(
                    "Cannot create a Purchase Order because this Sales Order has no lines."
                )
            )

        po_lines_cmds = self._spl_prepare_purchase_order_lines()
        if not po_lines_cmds:
            raise UserError(
                _("No valid products were found to purchase on this Sales Order.")
            )

        vendor = self._spl_get_default_vendor()
        if not vendor:
            raise UserError(
                _(
                    "Cannot create a Purchase Order because no vendor could be determined or created. "
                    "Please create at least one Vendor."
                )
            )

        po_vals = {
            "origin": self.name,
            "company_id": self.company_id.id,
            "currency_id": self.currency_id.id,
            "date_order": fields.Datetime.now(),
            "partner_id": vendor.id,
            "sale_order_id": self.id,
            "order_line": po_lines_cmds,
        }

        purchase_order = self.env["purchase.order"].create(po_vals)

        return {
            "type": "ir.actions.act_window",
            "name": _("Purchase Order"),
            "res_model": "purchase.order",
            "view_mode": "form",
            "res_id": purchase_order.id,
            "target": "current",
        }

    def action_view_purchase_orders(self):
        """
        Smart button handler: open related Purchase Orders.
        """
        self.ensure_one()
        orders = self.purchase_order_ids
        if not orders:
            raise UserError(_("No Purchase Orders are linked to this Sales Order."))

        if len(orders) == 1:
            return {
                "type": "ir.actions.act_window",
                "name": _("Purchase Order"),
                "res_model": "purchase.order",
                "view_mode": "form",
                "res_id": orders.id,
                "target": "current",
            }

        return {
            "type": "ir.actions.act_window",
            "name": _("Purchase Orders"),
            "res_model": "purchase.order",
            "view_mode": "list,form",
            "domain": [("id", "in", orders.ids)],
            "target": "current",
        }

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _spl_get_default_vendor(self):
        """
        Choose a default vendor so PO creation can succeed (partner_id is required).

        Default Case - First vendor from product template sellers (seller_ids.partner_id)
        Fallback Case - Any existing supplier (supplier_rank > 0)
            -> may need to swap with TBD Vendor,
            but the requirements on this logic was not precisely part of the exercise, so I am taking the liberty.
        No Vendor Case - Create a placeholder vendor 'TBD Vendor'
        """
        self.ensure_one()

        for line in self.order_line:
            product = line.product_id
            if not product:
                continue

            tmpl = getattr(product, "product_tmpl_id", False)
            seller_ids = getattr(tmpl, "seller_ids", False) if tmpl else False
            if not seller_ids:
                seller_ids = getattr(product, "seller_ids", False)

            if seller_ids:
                seller = seller_ids[:1]
                partner = getattr(seller, "partner_id", False)
                if partner:
                    return partner

        vendor = self.env["res.partner"].search([("supplier_rank", ">", 0)], limit=1)
        if vendor:
            return vendor

        try:
            return self.env["res.partner"].create(
                {"name": "TBD Vendor", "supplier_rank": 1}
            )
        except Exception:
            return False

    def _spl_prepare_purchase_order_lines(self):
        """
        Build purchase.order.line commands from sale.order.line.
        - purchase.order.line uses product_uom_id
        - sale.order.line uses product_uom_id
        """
        self.ensure_one()
        commands = []

        for line in self.order_line:
            product = line.product_id
            if not product:
                continue

            # minimal flow case
            if getattr(product, "type", None) == "service":
                continue

            tmpl = getattr(product, "product_tmpl_id", False)
            uom_po = getattr(tmpl, "uom_po_id", False) if tmpl else False
            if not uom_po:
                uom_po = getattr(line, "product_uom_id", False)
            if not uom_po:
                uom_po = getattr(product, "uom_id", False)

            if not uom_po:
                raise UserError(
                    _('Cannot determine a Unit of Measure for product "%s".')
                    % product.display_name
                )

            commands.append(
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "name": product.display_name,
                        "product_qty": line.product_uom_qty,
                        "product_uom_id": uom_po.id,
                        "price_unit": 0.0,
                        "date_planned": fields.Datetime.now(),
                    },
                )
            )

        return commands

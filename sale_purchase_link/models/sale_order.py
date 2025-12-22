# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_create_purchase_order(self):
        """
        Create a Purchase Order (RFQ) from this Sales Order.

        - Vendor default strategy:
            1) First available vendor on any product (seller_ids)
            2) Any existing supplier (supplier_rank > 0)
            3) Create a fallback supplier 'TBD Vendor'
        """
        self.ensure_one()

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
            # this should be rare, but keep a hard stop just in case that the vendor creation is blocked by access rules.
            raise UserError(
                _(
                    "Cannot create a Purchase Order because no vendor could be determined or created. "
                    "Please create at least one Vendor (res.partner with supplier_rank > 0)."
                )
            )

        po_vals = {
            "origin": self.name,
            "company_id": self.company_id.id,
            "currency_id": self.currency_id.id,
            "date_order": fields.Datetime.now(),
            "partner_id": vendor.id,  # required field on purchase.order -> may need to overwrite this, or just default to a value
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

    def _spl_get_default_vendor(self):
        """
        Choose a default vendor so PO creation can succeed (partner_id is required).
        """
        self.ensure_one()

        # 1) Try to find vendor from products' seller lists.
        # seller_ids usually live on product.template, but may be reachable from product.product too.
        for line in self.order_line:
            product = line.product_id
            if not product:
                continue

            # Prefer template sellers for compatibility.
            tmpl = getattr(product, "product_tmpl_id", False)
            seller_ids = getattr(tmpl, "seller_ids", False) if tmpl else False
            if not seller_ids:
                seller_ids = getattr(product, "seller_ids", False)

            # seller record field name is typically `partner_id`
            if seller_ids:
                seller = seller_ids[:1]
                partner = getattr(seller, "partner_id", False)
                if partner:
                    return partner

        # fallback: any supplier in the system.
        vendor = self.env["res.partner"].search([("supplier_rank", ">", 0)], limit=1)
        if vendor:
            return vendor

        # last resort: create a placeholder vendor (keeps the flow working).
        try:
            return self.env["res.partner"].create(
                {
                    "name": "TBD Vendor",
                    "supplier_rank": 1,
                }
            )
        except Exception:
            return False

    def _spl_prepare_purchase_order_lines(self):
        """
        Build purchase.order.order_line commands from sale.order.line.
        """
        self.ensure_one()
        commands = []

        for line in self.order_line:
            product = line.product_id
            if not product:
                continue

            # Skip services for this minimal flow.
            if getattr(product, "type", None) == "service":
                continue

            # resolve purchase UoM robustly:
            # most specific case: product.product_tmpl_id.uom_po_id (if present)
            # broader case: line.product_uom_id
            # general fallback: product.uom_id
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

            line_vals = {
                "product_id": product.id,
                "name": product.display_name,
                "product_qty": line.product_uom_qty,
                "product_uom_id": uom_po.id,
                "price_unit": 0.0,
                "date_planned": fields.Datetime.now(),
            }
            commands.append((0, 0, line_vals))

        return commands

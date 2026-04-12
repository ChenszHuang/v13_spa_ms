from odoo import fields, models, api

class SpaOrder(models.Model):
    _name = "spa.order"
    _description = "Spa Order"

    partner_id = fields.Many2one("res.partner", string="Customer", copy=False)
    order_line_ids = fields.One2many("spa.session", "order_id", string="Spa Sessions", copy=False)
    state = fields.Selection([
        ("draft", "Draft"),
        ("wait", "Waiting List"),
        ("confirm", "Confirmed"),
        ("done", "Payment Received"),
        ("cancel", "Cancelled"),
        ], string="Status", readonly=True, copy=False, index=True, default="draft")
    invoice_id = fields.Many2one("account.move", string="Invoice/Receipt")
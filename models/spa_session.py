from odoo import fields, models, api

class SpaSession(models.Model):
    _name = "spa.session"
    _description = "Spa Session"
    _order = "id desc"

    order_id = fields.Many2one("spa.order", string="Spa Order", copy=False)
    product_id = fields.Many2one("product.product", string="Treatment", copy=False, required=True)
    therapist_id = fields.Many2one("res.partner", string="Therapist", copy=False, required=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("wait", "Waiting"),
        ("ongoing", "Ongoing"),
        ("done", "Done"),
        ("cancel", "Cancelled"),
        ], string="Status", readonly=True, copy=False, index=True, default="draft")
    start_time = fields.Datetime(string="Start Time")
    end_time = fields.Datetime(string="End Time")
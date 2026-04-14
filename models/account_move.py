from odoo import fields, models, api

class AccountMove(models.Model):
    _inherit = "account.move"
    _order = "id desc"

    spa_order_id = fields.Many2one("spa.order", string="Order", tracking=True, copy=False)
    therapist_id = fields.Many2one("res.partner", string="Therapist", tracking=True, copy=False)
    

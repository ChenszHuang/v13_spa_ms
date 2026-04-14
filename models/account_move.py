from odoo import fields, models, api

class AccountMove(models.Model):
    _inherit = "account.move"

    spa_order_id = fields.Many2one('spa.order', string="Order", tracking=True, copy=False)

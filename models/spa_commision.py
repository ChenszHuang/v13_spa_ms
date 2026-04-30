from odoo import fields, models, api

class SpaCommission(models.Model):
    _name = "spa.commission"
    _inherit = ["mail.thread","mail.activity.mixin"]
    _description = "Spa Commission"

    partner_id = fields.Many2one("res.partner", required=True)
    product_id = fields.Many2one("product.product", required=True)
    commission_type = fields.Selection([
        ("fixed", "Fixed"),
        ("percent", "Percentage")
    ])
    amount = fields.Float()

    _sql_constraints = [
        ('partner_product_unique',
        'unique(partner_id, product_id)',
        'Commission for this partner and product already exists!')
    ]
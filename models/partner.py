from odoo import fields, models, api


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"
    
    is_therapist = fields.Boolean("Is Therapist", tracking=True, copy=False)
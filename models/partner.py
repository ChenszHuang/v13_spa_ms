from odoo import fields, models, api
from ..tools import const

class ResPartner(models.Model):
    _inherit = "res.partner"
    
    number = fields.Char(string="Therapist No.", readonly=True, tracking=True, copy=False, index=True)
    nickname = fields.Char(string="Nickname")
    gender = fields.Selection(const.GENDER_SELECTION, string="Gender", tracking=True)
    birthday = fields.Date(string="Date of Birth", tracking=True)
    marital = fields.Selection([
		("single", "Single"),
		("married", "Married"),
		("widowed", "Widowed"),
		("divorced", "Divorced"),
		], "Marital Status")
    is_therapist = fields.Boolean("Is Therapist", tracking=True, copy=False)
    is_guide = fields.Boolean("Is Guide", tracking=True, copy=False)
    join_date = fields.Date(string="Join Date", tracking=True, copy=False)
    therapist_code = fields.Char(string="Therapist ID", tracking=True, copy=False)
    
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        company = self.env.company
        if company.default_account_receivable:
            res['property_account_receivable_id'] = company.default_account_receivable.id
        if company.default_account_payable:
            res['property_account_payable_id'] = company.default_account_payable.id
        return res
    
    @api.model
    def create(self, vals):
        
        if vals.get('is_therapist') and not vals.get('number'):
            vals['number'] = self.env['ir.sequence'].next_by_code('res.partner.profile')

        return super().create(vals)
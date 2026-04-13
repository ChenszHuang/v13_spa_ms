from odoo import fields, models, api


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"
    
    is_therapist = fields.Boolean("Is Therapist", tracking=True, copy=False)
    
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        company = self.env.company
        if company.default_account_receivable:
            res['property_account_receivable_id'] = company.default_account_receivable.id
        if company.default_account_payable:
            res['property_account_payable_id'] = company.default_account_payable.id
        return res
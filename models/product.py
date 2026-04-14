from odoo import fields, models, api



class TreatmentType(models.Model):
    _name = "treatment.type"
    _description = "Treatment Type"

    name = fields.Char(string="Name", tracking=True, copy=False, index=True, required=True)
    code = fields.Char(string="Treatment Code", tracking=True, copy=False, index=True,required=True)
    treatment_ids = fields.One2many("product.template", "treatment_type_id", string="Treatments", ondelete="set null", copy=False)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    treatment_code = fields.Char("Treatment Code", required=True, tracking=True, copy=False) 
    duration = fields.Integer(string="Treatment Duration", required=True, tracking=True, copy=False, help="Treatment duration in minutes")
    treatment_type_id = fields.Many2one("treatment.type", string="Treatment Type", tracking=True, copy=False)

    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        company = self.env.company
        if company.default_property_account_income_id:
            res['property_account_income_id'] = company.default_property_account_income_id.id
        if company.default_property_account_expense_id:
            res['property_account_expense_id'] = company.default_property_account_expense_id.id
        return res


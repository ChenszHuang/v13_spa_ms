from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class PayoutCommission(models.TransientModel):
    _name = "print.payout.commission.report"
    _description = "Print Payout Commission Report"

    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)
    
    
    @api.onchange('date_from')
    def _onchange_date_from(self):
        if self.date_from:
             self.date_to = self.date_from.replace(day=1) + relativedelta(months=1, days=-1)
             

    def action_print(self):
        return self.env.ref('v13_spa_ms.action_payout_commission_report').report_action(self)
    
    
    def _get_report_base_filename(self):
        date_from = self.date_from.strftime('%d-%m-%Y')
        date_to = self.date_to.strftime('%d-%m-%Y')

        return f'City Sport Payout Commission Report ({date_from}-{date_to})'
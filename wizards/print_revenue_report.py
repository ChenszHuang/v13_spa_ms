from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class RevenueReport(models.TransientModel):
    _name = "print.revenue.report"
    _description = "Print Revenue Report"

    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)

    @api.onchange('date_from')
    def _onchange_date_from(self):
        if self.date_from:
             self.date_to = self.date_from.replace(day=1) + relativedelta(months=1, days=-1)

    
    def action_print(self):
        data = self.read(['date_from','date_to'])[0]
        return self.env.ref('v13_spa_ms.action_revenue_report').report_action(self)

    def _get_report_base_filename(self):
        date_from = self.date_from.strftime('%d-%m-%Y')
        date_to = self.date_to.strftime('%d-%m-%Y')

        return f'City Sport Revenue Report ({date_from}-{date_to})'
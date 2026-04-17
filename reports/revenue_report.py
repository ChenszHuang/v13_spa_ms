from odoo import models, fields, api

class RevenueReportAbstract(models.AbstractModel):
    _name = "report.v13_spa_ms.revenue_report"
    _description = "Revenue Report Abstract"


    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['print.revenue.report'].browse(docids)
        
        return {
        'doc_ids': docids,
        'doc_model': 'print.revenue.report',
        'docs': docs,
        'data': data,
    }

        
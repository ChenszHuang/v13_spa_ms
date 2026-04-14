from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = "res.company"
    
    #Accounting fields
    default_account_receivable = fields.Many2one("account.account", string="Default Account Receivable")
    default_account_payable = fields.Many2one("account.account", string="Default Account payable")
    default_property_account_income_id = fields.Many2one("account.account", string="Default Account Income")
    default_property_account_expense_id = fields.Many2one("account.account", string="Default Account Expense")
    default_invoice_payment_term_id = fields.Many2one("account.payment.term", string="Default Payment Term")

    #Journals
    default_invoice_journal_id = fields.Many2one("account.journal", string="Default Invoice Journal")

from odoo import fields, models, api
from odoo.exceptions import UserError

class AccountPayment(models.Model):
    _inherit = 'account.payment'
   

    @api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id')
    def _compute_destination_account_id(self):
        for payment in self:
            payment.destination_account_id = False

            # 1. PRIORITAS: dari invoice
            if payment.invoice_ids:
                accounts = payment.invoice_ids.mapped('line_ids.account_id').filtered(
                    lambda acc: acc.user_type_id.type in ('receivable', 'payable')
                )
                payment.destination_account_id = accounts[:1].id if accounts else False
                continue

            # 2. Transfer
            if payment.payment_type == 'transfer':
                transfer_acc = payment.company_id.transfer_account_id
                if not transfer_acc:
                    raise UserError(_('Please define a Transfer Account.'))
                payment.destination_account_id = transfer_acc.id
                continue

            # 3. Partner
            if payment.partner_id:
                if payment.partner_type == 'customer':
                    account = payment.partner_id.property_account_receivable_id or payment.company_id.default_account_receivable
                else:
                    account = payment.partner_id.property_account_payable_id or payment.company_id.default_account_payable

                payment.destination_account_id = account.id if account else False
                continue

            # 4. Fallback ke company custom field (INI BEDANYA DARI ODOO DEFAULT)
            if payment.partner_type == 'customer':
                account = payment.company_id.default_account_receivable
            elif payment.partner_type == 'supplier':
                account = payment.company_id.default_account_payable
            else:
                account = False

            payment.destination_account_id = account.id if account else False

    def post(self):
        
        # Redirect ke record payment setelah post
        for payment in self:
            if payment.payment_type == 'inbound' and payment.partner_type == 'customer':
                    if not payment.name or payment.name == "/":
                        payment.name = self.env['ir.sequence'].next_by_code('customer.payment') 
                        
            result = super().post()

            for invoice in payment.invoice_ids:
                if invoice.spa_order_id:
                    if invoice.invoice_payment_state == "paid" and invoice.spa_order_id.state != "cancel":
                        invoice.spa_order_id.write({
                            "state": "done",
                        })

            if len(self) == 1:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.payment',
                    'res_id': self.id,
                    'view_mode': 'form',
                    'target': 'current',
                    'views': [(self.env.ref('v13_spa_ms.view_account_payment_form_custom').id, 'form')],
                }
            return result
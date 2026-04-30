from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError

class SpaOrder(models.Model):
    _name = "spa.order"
    _inherit = ["mail.thread","mail.activity.mixin"]
    _description = "Spa Order"
    _rec_name = "number"
    _order = "id desc"

    number = fields.Char(string="Number", copy=False, readonly=True)
    partner_id = fields.Many2one("res.partner", string="Customer", copy=False, required=True, tracking=True)
    guide_id = fields.Many2one("res.partner", string="Guide", copy=False, tracking=True)
    date = fields.Date(string="Date", tracking=True, copy=False, default=fields.Date.context_today)
    spa_session_ids = fields.One2many("spa.session", "spa_order_id", string="Spa Sessions", copy=False)
    reference = fields.Char(string="Reference")
    treatment_count = fields.Integer(string="Treatment Count", compute="_compute_treatment_count", store=True)
    
    state = fields.Selection([
        ("draft", "Draft"),
        ("wait", "Waiting List"),
        ("confirm", "Confirmed"),
        ("done", "Payment Received"),
        ("cancel", "Cancelled"),
        ], string="Status", readonly=True, copy=False, index=True, tracking=True, default="draft")
    invoice_ids = fields.One2many("account.move", "spa_order_id", string="Invoice/Receipt")
    

    #api model

    @api.depends('spa_session_ids.state')
    def _compute_treatment_count(self):
        for record in self:
            confirmed_sessions = record.spa_session_ids.filtered(lambda s: s.state in ['ongoing', 'done'])
            record.treatment_count = len(confirmed_sessions)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        partner = self.env.ref('v13_spa_ms.partner_kontan', raise_if_not_found=False)
        if partner:
            res['partner_id'] = partner.id
        return res

    def name_get(self):
        result = []
        for record in self:
            name = record.number or (f"New Order (*{record.id})" if isinstance(record.id, int) else "New Order")
            result.append((record.id, name))

        return result


    def action_waitlist(self):
        for record in self:
            
            if record.state not in ["draft"]:
                raise UserError("State is not in draft status, please refresh")
            
            for session in record.spa_session_ids:
                session.write({
                    "state": "wait"
                })
            record.write({"state":"wait"})

    def action_confirm(self):
        for record in self:
            date = record.date
            
            if record.state not in ["draft", "wait"]:
                raise UserError("State is not in draft/waiting list status, please refresh")
            
            if not record.number:
                record.number = self.env["ir.sequence"].next_by_code("spa.order")
                
            for session in record.spa_session_ids:
                session.write({
                    "state": "ongoing"
                })
            if not record.invoice_ids:
                record.create_and_post_customer_invoice(date=date)
            else:
                record.update_existing_invoice(invoice=record.invoice_ids[0], date=date)
            
            record.write({"state":"confirm"})

    def action_cancel(self):
        for record in self:
            if record.state not in ["draft", "wait", "confirm","done"]:
                raise UserError("State is updated, please refresh")
            
            for session in record.spa_session_ids:
                session.write({
                    "state": "cancel"
                })
            record.cancel_existing_payment()
            record.write({"state":"cancel"})
            
            
    def action_draft(self):
        for record in self:
            if record.state not in ["cancel"]:
                raise UserError("State is updated, please refresh")
            
            for session in record.spa_session_ids:
                session.write({
                    "state": "draft"
                })
            for invoice in record.invoice_ids:
                invoice.write({
                    "state":"draft"
                })
            record.write({"state":"draft"})
            
    def cancel_existing_payment(self):
        for record in self:
            for invoice in record.invoice_ids:
                if invoice.invoice_payment_state == 'paid':
                    for payment in invoice.payment_ids:
                        payment.cancel()
                    lines = invoice.line_ids.filtered(lambda l: l.account_id.reconcile)
                    if lines:
                        lines.remove_move_reconcile()
    
    def create_and_post_customer_invoice(self,date=None):
        ctx = self._context
        partner = self.partner_id
        company = self.env.company
        
        AccountMove = self.env["account.move"].with_context(default_type="out_invoice")
        journal = company.default_invoice_journal_id
        lines = self.get_invoice_lines()

        values = {
            "type": "out_invoice",
            "invoice_date": date or fields.Date.context_today(self),
            "partner_id":partner.id,
            "invoice_payment_term_id":company.default_invoice_payment_term_id,
            "journal_id":journal.id,
            "invoice_line_ids": lines,
            "spa_order_id":self.id,
            "guide_id":self.guide_id.id,
            "ref":self.reference,
        }

        invoice = AccountMove.create(values)
        invoice.action_post() 
        return invoice

    def update_existing_invoice(self, invoice=None, date=None):
        company = self.env.company
        partner = self.partner_id
        journal = company.default_invoice_journal_id
        lines = self.get_invoice_lines()
        
        invoice.write({
            "invoice_date": date or fields.Date.context_today(self),
            "partner_id": partner.id,
            "invoice_payment_term_id": company.default_invoice_payment_term_id.id,
            "journal_id": journal.id,
            "invoice_line_ids": [(5, 0, 0)] + lines,
            "spa_order_id": self.id,
            "guide_id": self.guide_id.id,
            "ref":self.reference,
        })
        invoice._recompute_dynamic_lines()

    def get_invoice_lines(self):
        invoice_lines = []

        for record in self:
            groups = {}
            for session in record.spa_session_ids:
                if not session.product_id:
                    continue
                    
                product = session.product_id
                partner = session.partner_id
                commission = self.env['spa.commission'].search([
                    ('product_id', '=', product.id),
                    ('partner_id', '=', partner.id)
                ], limit=1)
                commission_rate = commission.amount 
                price = product.list_price
                discount = session.discount or 0.0
                
                key = (product.id, price, discount)
                
                if key not in groups:
                    account = (product.property_account_income_id or product.categ_id.property_account_income_categ_id)
                
                    if not account:
                        raise UserError("Product has no income account.")
                
                    groups[key] = {
                        'product_id': product.id,
                        'name': product.name,
                        'price_unit': price,
                        'commission_rate': commission_rate,
                        'quantity': 0,
                        'account_id': account.id,
                        'discount': discount,
                    }
                groups[key]['quantity'] += 1

            for line_vals in groups.values():
                invoice_lines.append((0, 0, line_vals))

        return invoice_lines
    


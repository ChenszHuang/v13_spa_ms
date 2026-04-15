from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError

class SpaOrder(models.Model):
    _name = "spa.order"
    _inherit = ["mail.thread","mail.activity.mixin"]
    _description = "Spa Order"
    _rec_name = "number"
    _order = "id desc"

    number = fields.Char(string="Number", copy=False, readonly=True)
    partner_id = fields.Many2one("res.partner", string="Customer", copy=False, required=True)
    date = fields.Date(string="Date", tracking=True, copy=False, default=fields.Date.context_today)
    spa_session_ids = fields.One2many("spa.session", "spa_order_id", string="Spa Sessions", copy=False)
    reference = fields.Char(string="Reference")
    treatment_count = fields.Integer(string="Treatment Count", compute="_compute_treatment_count", store=False)
    
    state = fields.Selection([
        ("draft", "Draft"),
        ("wait", "Waiting List"),
        ("confirm", "Confirmed"),
        ("done", "Payment Received"),
        ("cancel", "Cancelled"),
        ], string="Status", readonly=True, copy=False, index=True, tracking=True, default="draft")
    invoice_ids = fields.One2many("account.move", "spa_order_id", string="Invoice/Receipt")
    

    #api model

    @api.depends('spa_session_ids')
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
            record.create_and_post_customer_invoice(date=date)
            
            record.write({"state":"confirm"})

    def action_cancel(self):
        for record in self:
            if record.state not in ["draft", "wait", "confirm"]:
                raise UserError("State is not in draft/waiting/Confirmed status, please refresh")
            
            for session in record.spa_session_ids:
                session.write({
                    "state": "cancel"
                })
            record.write({"state":"cancel"})
    
    
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
        }

        invoice = AccountMove.create(values)
        invoice.action_post() 
        return invoice

    def get_invoice_lines(self):
        invoice_lines = []

        for record in self:
            for session in record.spa_session_ids:
                if not session.product_id:
                    continue
            
                product = session.product_id
                account = (product.property_account_income_id or product.categ_id.property_account_income_categ_id)
                
                if not account:
                    raise UserError("Product has no income account.")
                
                invoice_line_vals = {
                    "product_id": product.id,
                    "name": product.name,
                    "price_unit":product.list_price,
                    "quantity": session.quantity if hasattr(session, "quantity") else 1,
                    "account_id": account.id,
                    "discount":session.discount,
                }
                
                invoice_lines.append((0, 0, invoice_line_vals))

        return invoice_lines
    


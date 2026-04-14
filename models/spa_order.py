from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError

class SpaOrder(models.Model):
    _name = "spa.order"
    _inherit = ["mail.thread","mail.activity.mixin"]
    _description = "Spa Order"
    _rec_name = "number"

    number = fields.Char(string="Number", copy=False, readonly=True)
    partner_id = fields.Many2one("res.partner", string="Customer", copy=False)
    date = fields.Date(string="Date", tracking=True, copy=False, default=fields.Date.context_today)
    spa_session_ids = fields.One2many("spa.session", "spa_order_id", string="Spa Sessions", copy=False)
    reference = fields.Char(string="Reference")
    
    state = fields.Selection([
        ("draft", "Draft"),
        ("wait", "Waiting List"),
        ("confirm", "Confirmed"),
        ("done", "Payment Received"),
        ("cancel", "Cancelled"),
        ], string="Status", readonly=True, copy=False, index=True, tracking=True, default="draft")
    invoice_ids = fields.One2many("account.move", "spa_order_id", string="Invoice/Receipt")

    #api model
    

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
    
    
    def create_and_post_customer_invoice(self,date=None):
        ctx = self._context
        
        AccountMove = self.env["account.move"].with_context(default_type="out_invoice")
         
        values = {
            "type": "out_invoice",
            "invoice_date": date or fields.Date.context_today(self),
            
            
        }
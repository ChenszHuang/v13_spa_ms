from odoo import fields, models, api
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import timedelta

class WizardBatchSession(models.TransientModel):
    _name = "wizard.batch.session"
    _description = "Wizard Batch Session"

    spa_order_id = fields.Many2one("spa.order", string="Spa Order", required=True)
    line_ids = fields.One2many("wizard.batch.session.line", "wizard_id", string="Session Lines",)

    def action_confirm(self):
        self.ensure_one()

        if not self.line_ids:
            raise UserError("Tambahkan minimal 1 baris treatment.")

        new_sessions = []

        for line in self.line_ids:
            if not line.therapist_ids:
                raise UserError(f"Treatment '{line.product_id.name}' belum memiliki therapist.")

            for therapist in line.therapist_ids:
                new_sessions.append((0, 0, {
                    "spa_order_id": self.spa_order_id.id,
                    "product_id": line.product_id.id,
                    "product_price": line.product_price,
                    "discount": line.discount,
                    "therapist_id": therapist.id,
                    "start_time": line.start_time,
                    "state": "draft",
                }))
 
        self.spa_order_id.write({"spa_session_ids": new_sessions})

class WizardBatchSessionLine(models.TransientModel):
    _name = "wizard.batch.session.line"
    _description = "Wizard Batch Session Line"
 
    wizard_id = fields.Many2one("wizard.batch.session", required=True, ondelete="cascade")
    product_id = fields.Many2one("product.product", string="Treatment", required=True)
    product_price = fields.Float(string="Price",compute="_compute_product_price", store=True)
    duration = fields.Integer(string="Duration (min)")
    discount = fields.Float(string="Discount (%)")
    start_time = fields.Datetime(string="Start Time", required=True, default=fields.Datetime.now)
    end_time = fields.Datetime(string="End Time", compute="_compute_end_time", store=True)
    therapist_ids = fields.Many2many(
        "res.partner",
        "wizard_batch_line_therapist_rel",
        "line_id",
        "therapist_id",
        string="Therapists",
    )
    qty = fields.Integer(string="Qty", compute="_compute_qty")
 

    @api.depends("therapist_ids")
    def _compute_qty(self):
        for rec in self:
            rec.qty = len(rec.therapist_ids)
 
    @api.depends("start_time", "duration")
    def _compute_end_time(self):
        for rec in self:
            if rec.start_time and rec.duration:
                rec.end_time = rec.start_time + timedelta(minutes=rec.duration)
            else:
                rec.end_time = False
 
    @api.depends("product_id")
    def _compute_product_price(self):
        if self.product_id:
            self.product_price = self.product_id.list_price
            self.duration = self.product_id.duration
        else:
            self.product_price = 0.0
            self.duration = 0



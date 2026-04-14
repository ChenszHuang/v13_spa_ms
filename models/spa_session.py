from odoo import fields, models, api
from datetime import timedelta
from odoo.exceptions import AccessError, UserError, ValidationError

class SpaSession(models.Model):
    _name = "spa.session"
    _description = "Spa Session"
    _order = "id desc"

    spa_order_id = fields.Many2one("spa.order", string="Spa Order", copy=False)
    product_id = fields.Many2one("product.product", string="Treatment", copy=False, required=True)
    therapist_id = fields.Many2one("res.partner", string="Therapist", copy=False, required=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("wait", "Waiting"),
        ("ongoing", "Ongoing"),
        ("done", "Done"),
        ("cancel", "Cancelled"),
        ], string="Status", readonly=True, copy=False, index=True, default="draft")
    start_time = fields.Datetime(string="Start Time", default=fields.Datetime.now)
    end_time = fields.Datetime(string="End Time", compute="_compute_end_time", store=True, tracking=True, copy=False)


    #api decorator

    @api.constrains('start_time', 'product_id', 'therapist_id')
    def _check_therapist_availability(self):
        for record in self:
            if not record.start_time or not record.product_id or not record.therapist_id:
                continue

            end_time = record.start_time + timedelta(minutes=record.product_id.duration or 0)

            domain = [
                ('therapist_id', '=', record.therapist_id.id),
                ('state', 'in', ['wait', 'ongoing']),
                ('start_time', '<', end_time),
                ('end_time', '>', record.start_time),
            ]

            if record.id:
                domain.append(('id', '!=', record.id))

            conflict = self.env['spa.session'].search(domain, limit=1)
            if conflict:
                raise ValidationError(
                    f"Therapist {record.therapist_id.name} sudah memiliki sesi pada "
                    f"{conflict.start_time.strftime('%d/%m/%Y %H:%M')} - "
                    f"{conflict.end_time.strftime('%H:%M')}. "
                    f"Silakan pilih therapist lain atau ubah waktu."
                )

    @api.depends('start_time', 'product_id')
    def _compute_end_time(self):
        for record in self:
            if record.start_time and record.product_id and record.product_id.duration:
                record.end_time = record.start_time + timedelta(
                    minutes=record.product_id.duration
                )
            else:
                record.end_time = False

    #button state
    def action_waitlist(self):
        for record in self:
            if record.state not in ['draft']:
                raise UserError("State is not in draft status, please refresh & try again")
                
            record.write({'state':'wait'})
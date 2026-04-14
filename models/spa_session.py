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
    unavailable_therapist_ids = fields.Many2many("res.partner",compute="_compute_unavailable_therapist")
    state = fields.Selection([
        ("draft", "Draft"),
        ("wait", "Waiting"),
        ("ongoing", "Ongoing"),
        ("done", "Done"),
        ("cancel", "Cancelled"),
        ], string="Status", readonly=True, copy=False, index=True, default="draft")
    start_time = fields.Datetime(string="Start Time", default=fields.Datetime.now)
    end_time = fields.Datetime(string="End Time", compute="_compute_end_time", store=True, tracking=True, copy=False)


    #api.depends

    @api.depends('start_time', 'end_time', 'spa_order_id.spa_session_ids.therapist_id')
    def _compute_unavailable_therapist(self):
        for record in self:
            domain = [
                ('state', 'in', ['wait', 'ongoing']),
                ('start_time', '<', record.end_time),
                ('end_time', '>', record.start_time),
            ]
            if record.id:
                domain.append(('id', '!=', record.id))

            sessions = self.env['spa.session'].search(domain)
            busy_therapists = sessions.mapped('therapist_id')

            used_therapists = record.spa_order_id.spa_session_ids.filtered(lambda s: s.id != record.id).mapped('therapist_id')
            
            record.unavailable_therapist_ids = busy_therapists | used_therapists

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
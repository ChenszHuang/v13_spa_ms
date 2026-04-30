from odoo import fields, models, api
from odoo.fields import Datetime
from datetime import timedelta
from odoo.exceptions import AccessError, UserError, ValidationError

class SpaSession(models.Model):
    _name = "spa.session"
    _inherit = ["mail.thread","mail.activity.mixin"]
    _description = "Spa Session"
    _order = "id desc"

    spa_order_id = fields.Many2one("spa.order", string="Spa Order", copy=False, tracking=True)
    guide_id = fields.Many2one("res.partner", related="spa_order_id.guide_id", store=True, tracking=True)
    product_id = fields.Many2one("product.product", string="Treatment", copy=False, required=True, tracking=True)
    product_price = fields.Float(string="Price", readonly=True)
    duration = fields.Integer(string="Duration", related="product_id.duration")
    discount = fields.Float(string="Discount",tracking=True, copy=False, index=True)
    total_amount = fields.Float(string="Total", compute="_compute_total_amount", store="True")
    therapist_id = fields.Many2one("res.partner", string="Therapist", copy=False, required=True, tracking=True, index=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("wait", "Waiting"),
        ("ongoing", "Started"),
        ("done", "Done"),
        ("cancel", "Cancelled"),
        ], string="Status", readonly=True, copy=False, index=True, tracking=True, default="draft")
    start_time = fields.Datetime(string="Start Time", default=fields.Datetime.now, tracking=True, required=True)
    end_time = fields.Datetime(string="End Time", compute="_compute_end_time", store=True, tracking=True, copy=False)
    remarks = fields.Text(string="Remarks", copy=False)
    commission_amount = fields.Float(string="Commission Amount",compute="_compute_commission", store=True)
    partner_id = fields.Many2one("res.partner", related="spa_order_id.partner_id", store=True, tracking=True)



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
                start_time = Datetime.context_timestamp(self, conflict.start_time)
                end_time_conflict = Datetime.context_timestamp(self, conflict.end_time)

                raise ValidationError(
                    f"Therapist {record.therapist_id.name} sudah memiliki sesi pada "
                    f"{start_time.strftime('%d/%m/%Y %H:%M')} - "
                    f"{end_time_conflict.strftime('%H:%M')}. "
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

    @api.depends("product_price", "discount")
    def _compute_total_amount(self):
        for record in self:
            price = record.product_price or 0.0
            discount = record.discount or 0.0

            record.total_amount = price * (1 - (discount / 100.0))

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_price = self.product_id.list_price
            self.duration = self.product_id.duration
    
    @api.depends('product_id', 'spa_order_id.partner_id')
    def _compute_commission(self):
        for rec in self:
            rec.commission_amount = 0

            if not rec.product_id or not rec.spa_order_id.partner_id:
                continue

            config = self.env['spa.commission'].search([
                ('partner_id', '=', rec.spa_order_id.partner_id.id),
                ('product_id', '=', rec.product_id.id)
            ], limit=1)

            price = rec.product_price

            if config:
                if config.commission_type == 'fixed':
                    rec.commission_amount = config.amount
                else:
                    rec.commission_amount = price * config.amount / 100

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.spa_order_id.number} - {record.therapist_id.name}"
            result.append((record.id, name))

        return result

    #button state
    def action_waitlist(self):
        for record in self:
            if record.state not in ['draft']:
                raise UserError("State is not in draft status, please refresh & try again")
                
            record.write({'state':'wait'})

    def action_start(self):
        for record in self:
            if record.state not in ['draft', 'wait']:
                raise UserError("State is not in draft/waiting status, please refresh & try again")
                
            record.write({'state':'ongoing'})

    def action_cancel(self):
        for record in self:
            record.write({'state':'cancel'})
    
    def action_draft(self):
        for record in self:
            if record.state not in ['cancel']:
                raise UserError("State is not in cancel status, please refresh & try again")

            record.write({'state':"draft"})
    
    def action_done(self):
        for record in self:
            if record.state not in ["ongoing"]:
                raise UserError("State is not in started status, please refresh & try again")
            
            if record.end_time > fields.Datetime.now():
                raise UserError("The session cannot be completed yet. Please wait until the end time.")
            
            record.write({"state": "done"})

    def _cron_session_status(self):

        now = fields.Datetime.now()

        sessions = self.search([
            ('state', 'in', ['ongoing']),
            ('end_time', '<', now)
        ])

        sessions.write({
            'state': 'done'
        })

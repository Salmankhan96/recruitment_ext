from email.policy import default

from odoo import models, fields, api
from odoo.exceptions import UserError

class SendTemplateWizard(models.TransientModel):
    _name = 'send.template.wizard'
    _description = 'Send Template Wizard'

    selection_type = fields.Selection([
        ('offer', 'Offer Letter')], default="offer" ,string="Type", required=True)

    template_id = fields.Many2one('mail.template', string="Mail Template", domain="[('model_id.model','=','hr.applicant')]", required=True)
    applicant_id = fields.Many2one('hr.applicant', string="Applicant", required=True)

    @api.onchange('selection_type')
    def _onchange_selection_type(self):
        if self.selection_type:
            subject_map = {
                'offer': 'Offer Letter'
            }
            subject_keyword = subject_map.get(self.selection_type)
            template = self.env['mail.template'].search([
                ('model_id.model', '=', 'hr.applicant'),
                ('subject', 'ilike', subject_keyword)
            ], limit=1)
            if template:
                self.template_id = template

    def action_send_email(self):
        template_id = self.env.ref('recruitment_ext.mail_template_offer_letter')
        template_id.send_mail(self.applicant_id.id, force_send=True)

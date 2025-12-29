from odoo import models, fields, api
from odoo.exceptions import UserError

class SendTemplateWizard(models.TransientModel):
    _name = 'send.template.wizard'
    _description = 'Send Template Wizard'

    selection_type = fields.Selection([
        ('jd', 'JD'),
        ('scheduled_interview', 'Scheduled Interview/Meet'),
        ('confirm_letter', 'Confirm Letter'),
        ('interview_result', 'Interview Result'),
    ], string="Type", required=True)

    template_id = fields.Many2one('mail.template', string="Mail Template", domain="[('model_id.model','=','hr.applicant')]", required=True)
    applicant_id = fields.Many2one('hr.applicant', string="Applicant", required=True)

    @api.onchange('selection_type')
    def _onchange_selection_type(self):
        if self.selection_type:
            subject_map = {
                'jd': 'JD',
                'scheduled_interview': 'Scheduled Interview',
                'confirm_letter': 'Confirm Letter',
                'interview_result': 'Interview Result',
            }
            subject_keyword = subject_map.get(self.selection_type)
            template = self.env['mail.template'].search([
                ('model_id.model', '=', 'hr.applicant'),
                ('subject', 'ilike', subject_keyword)
            ], limit=1)
            if template:
                self.template_id = template

    def action_send_email(self):
        if not self.template_id:
            raise UserError("No mail template selected!")

        if not self.applicant_id:
            raise UserError("No applicant selected!")

        self.template_id.send_mail(self.applicant_id.id, force_send=True)

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    checklist_ids = fields.Many2one(
        'employee.checklist')
    completed = fields.Boolean(
        string="Completed",
        help="Check this box when the item is completed."
    )


class EmployeeChecklistItem(models.Model):
    _name = 'employee.checklist'
    _description = 'Employee Onboarding Checklist Item'
    _rec_name = 'description'

    # employee_id = fields.One2many(
    #     'hr.employee',
    #     'checklist_ids',
    #     string="Employee"
    # )
    description = fields.Text(
        string="Description",
        help="Detailed description or instructions for this checklist item."
    )
    # sequence = fields.Integer(
    #     string="Sequence",
    #     default=10,
    #     help="Order in which the checklist items appear."
    # )
    # asset_allocation_laptop = fields.Char("IT/Admin assigns Laptops")
    # asset_allocation_other = fields.Char("IT/Admin assigns access card")
    # asset_allocation_soft_credential = fields.Char("Software Credential")

class HrEmployeeEmailWizard(models.TransientModel):
    _name = 'hr.employee.email.wizard'
    _description = 'Wizard to send email with document'

    email_to = fields.Char(string="Recipient Email", required=True)
    email_subject = fields.Char(string="Subject", required=True)
    email_body_html = fields.Html(string="Body")  # HTML field for rich text

    # Field for document upload
    attachment_file = fields.Binary(string="Upload Document")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    attachment_name = fields.Char(string="File Name")

    mail_template_id = fields.Many2one(
        'mail.template',
        string="Email Template",
        domain="[('model', '=', 'hr.employee')]"  # Restrict to templates for hr.employee
    )

    @api.model
    def default_get(self, fields_list):
        """
        Populate default values from the active employee.
        """
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            employee = self.env['hr.employee'].browse(active_id)
            if employee.exists():
                res['employee_id'] = employee.id
                res['email_to'] = employee.work_email or employee.private_email or employee.user_id.email
                res['email_subject'] = f"Regarding your Employment - {employee.name}"
                # You can set a default email body if needed
                res[
                    'email_body_html'] = f"<p>Dear {employee.name},</p><p>Please find the attached document.</p><p>Best regards,<br/>HR Team</p>"
        return res

    @api.onchange('mail_template_id')
    def _onchange_mail_template_id(self):
        """
        Update subject and body when a template is selected.
        """
        if self.mail_template_id:
            template = self.mail_template_id.with_context(lang=self.employee_id.user_id.lang or self.env.user.lang)
            # Render the template and apply values
            # Using generate_email to get a dictionary of values
            template_values = template._generate_template([self.employee_id.id], ['subject', 'body_html', 'email_to'])
            if template_values:
                self.email_subject = template_values[self.employee_id.id]['subject']
                self.email_body_html = template_values[self.employee_id.id]['body_html']
                # You might want to override email_to if the template has a specific one
                # self.email_to = template_values[self.employee_id.id].get('email_to', self.email_to)

    def action_send_email_with_attachment(self):
        """
        Sends the email with the uploaded attachment.
        """
        self.ensure_one()

        if not self.email_to:
            raise UserError(_("Recipient email is not specified."))
        if not self.email_subject:
            raise UserError(_("Email subject is empty."))

        # Prepare attachment if uploaded
        attachments = []
        if self.attachment_file and self.attachment_name:
            attachments.append((self.attachment_name, base64.b64decode(self.attachment_file)))

        # Create mail_mail record
        mail_vals = {
            'subject': self.email_subject,
            'body_html': self.email_body_html,
            'email_from': 'techrajendra25@gmail.com',
            'email_to': self.email_to,
            'recipient_ids': [(4, self.employee_id.user_id.partner_id.id)] if self.employee_id.user_id.partner_id else False,
            'model': 'hr.employee',
            'res_id': self.employee_id.id,
            'attachment_ids': [],
        }

        # If an attachment exists, create an ir.attachment record and link it
        if attachments:
            attachment_obj = self.env['ir.attachment']
            for name, data in attachments:
                attachment = attachment_obj.create({
                    'name': name,
                    'datas': base64.b64encode(data),
                    'res_model': 'hr.employee',
                    'res_id': self.employee_id.id,
                    'mimetype': 'application/octet-stream',
                })
                mail_vals['attachment_ids'].append((4, attachment.id))

        mail = self.env['mail.mail'].create(mail_vals)
        mail.send()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Email sent successfully!'),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

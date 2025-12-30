from odoo import models, fields, api
from odoo.exceptions import UserError

class HrPreOnboarding(models.Model):
    _name = 'hr.pre.onboarding'
    _description = 'Pre Onboarding Details'

    applicant_id = fields.Many2one('hr.applicant', string="Applicant", required=True, ondelete='cascade')
    name = fields.Char(string="Candidate Name", related='applicant_id.partner_name', store=True)
    email = fields.Char(string="Email", related='applicant_id.email_from', store=True)
    designation = fields.Char(string="Designation",related='applicant_id.name',store=True)
    department = fields.Char(string="Department")
    salary = fields.Integer(string="Salary (CTC)")
    location = fields.Char(string="Location")
    date_of_joining = fields.Date(string="D.O.J reported on duty")


    duly_sign_copy_of_emp = fields.Binary("Duly Signed copy of Employee LOA")
    resume_duly_sign_with_photo = fields.Binary("Resume duly signed with photo")
    all_educational_certificate_with_10th_12th = fields.Binary("All educational certificates and Marks sheet 10th, 12th &amp; Graduation")
    all_merits_certificate_diploma = fields.Binary("All Merit certificates/ Diploma mark sheet")
    acceptance_of_resign_letter = fields.Binary("Acceptance of Resignation letter")
    copy_of_relieving_letter = fields.Binary("Copy of Relieving letter/ Exp. Certificate")
    last_three_months_salary_slip = fields.Binary("Last 3 month salary slip / salary certificate")
    six_month_bank_statement = fields.Binary("6 months bank statement")
    previous_company_form16 = fields.Binary("Previous company Form 16 / PAN Card")
    address_proof = fields.Binary("1 Address Proof – D.L / Voter ID / Aadhar Card")
    id_proof = fields.Binary("1 ID proof -  PAN card / Passport")
    passport_size_photo = fields.Binary("Latest Four passport size color photograph")
    acceptance_of_offer_letter = fields.Binary("Acceptance of Offer letter")
    fitness_certificate = fields.Binary("Fitness Certificate")


    state = fields.Selection([
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('verified', 'Verified'),
    ], default='pending', string="Status")

    def action_mark_verified(self):
        self.ensure_one()
        # Create HR Employee
        self.env['hr.employee'].create({
            'name': self.name,
            'work_email': self.email,
            'job_title': self.applicant_id.job_id.name,
        })
        self.state = 'verified'

    def action_reject(self):
        self.ensure_one()
        self.state = 'rejected'

    def action_show_sign(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sign Documents',
            'res_model': 'sign.request',
            'view_mode': 'tree,form',
            'domain': [
                ('reference', '=', f'{self._name},{self.id}')
            ],
            'context': {
                'default_reference': f'{self._name},{self.id}',
            }
        }

from odoo import models, fields, api
from odoo.exceptions import UserError
import tempfile
import base64
import os
import pdfplumber
import re
import logging
import unicodedata
import difflib


_logger = logging.getLogger(__name__)


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    resume_attachment = fields.Binary(string="Resume")
    resume_filename = fields.Char(string="Resume Filename")

    education_details = fields.Text(string="Education")
    experience_details = fields.Text(string="Experience")
    experience_in_years = fields.Float(string="Experience")
    skills_details = fields.Text(string="Key Skills")
    certification_details = fields.Text(string="Certifications")
    project_details = fields.Text(string="Projects")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft')

    education_rating = fields.Selection(
        [('1', '⭐'), ('2', '⭐⭐'), ('3', '⭐⭐⭐'), ('4', '⭐⭐⭐⭐'), ('5', '⭐⭐⭐⭐⭐')],
        string="Education Rating"
    )
    experience_rating = fields.Selection(
        [('1', '⭐'), ('2', '⭐⭐'), ('3', '⭐⭐⭐'), ('4', '⭐⭐⭐⭐'), ('5', '⭐⭐⭐⭐⭐')],
        string="Experience Rating"
    )
    skill_rating = fields.Selection(
        [('1', '⭐'), ('2', '⭐⭐'), ('3', '⭐⭐⭐'), ('4', '⭐⭐⭐⭐'), ('5', '⭐⭐⭐⭐⭐')],
        string="Skill Rating"
    )
    offer_date = fields.Date(string="Offer Letter Date", default=fields.Date.context_today)
    candidate_address = fields.Char(string="Candidate Address")
    office_address = fields.Char(string="Office Address")
    salary_package = fields.Char(string="Salary Package")
    joining_date = fields.Date(string="Joining Date")
    hr_name = fields.Char(string="Hr Name")
    job_description = fields.Char("Job Description")
    interview_result = fields.Char("Interview Result")
    interview_date = fields.Date(string="Interview Date")
    interview_time = fields.Char(string="Interview Time")
    interview_location = fields.Char(string="Interview Location")
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    key_skills_require = fields.Many2many(
        'hr.skill',
        'job_skill_rel',
        'job_id',
        'skill_id',
        string='Key Skills Required'
    )

    education_required = fields.Many2many(
        'hr.education',
        'job_education_rel',
        'job_id',
        'education_id',
        string='Education Required'
    )

    experience_required = fields.Many2many(
        'hr.experience',
        'job_experience_rel',
        'job_id',
        'experience_id',
        string='Experience Required'
    )

    show_send_offer = fields.Boolean(compute='_compute_show_send_offer', store=True)
    note = fields.Html(string='Mail Content')
    pre_onboarding_id = fields.One2many('hr.pre.onboarding', 'applicant_id', string="Pre-Onboarding Form")

    @api.depends('state')
    def _compute_show_send_offer(self):
        for rec in self:
            rec.show_send_offer = rec.state == 'approved'

    def action_approve(self):
        for rec in self:
            if not self.env.user.has_group('hr.group_hr_manager'):
                raise UserError("Only HR Managers can approve.")
            rec.state = 'approved'

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

    def action_parse_resume(self):
        for rec in self:
            if not rec.resume_attachment:
                raise UserError("⚠ Please upload a resume before clicking 'Parse Resume'.")

            try:
                # Save resume temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(base64.b64decode(rec.resume_attachment))
                    tmp_path = tmp_file.name

                # Extract text
                with pdfplumber.open(tmp_path) as pdf:
                    text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

                # Use parser
                result = rec._extract_resume_details(text)

                # Write extracted data to applicant
                rec.write({
                    'partner_name': result.get('name') or rec.partner_name,
                    'email_from': result.get('email') or rec.email_from,
                    'education_details': result.get('education') or result.get('education_match'),
                    'experience_details': result.get('experience') or result.get('experience_match'),
                    'experience_in_years': result.get('experience_in_years'),
                    'skills_details':result.get('skills_match'),
                    'certification_details':result.get('certifications_match'),
                    'project_details':result.get('projects_match'),
                    'partner_phone':result.get('mobile'),
                    'partner_mobile':result.get('mobile'),
                    'linkedin_profile':result.get('social_links'),
                    'education_rating': '4',
                    'experience_rating': '4',
                    'skill_rating': '4',
                })

                # Also write mobile to related partner, if available
                if rec.partner_id and result.get('mobile'):
                    rec.partner_id.write({'mobile': result.get('mobile')})

                os.unlink(tmp_path)

            except Exception as e:
                raise UserError(f"❌ Failed to parse resume:\n{str(e)}")

    def _extract_resume_details(self, text):
        result = {
            'email': '',
            'mobile': '',
            'name': '',
            'degree': [],
            'education': '',
            'experience': '',
            'skills':'',
            'certifications':'',
            'projects':''
        }

        lines = text.strip().splitlines()
        text_lower = text.lower()

        # --- Name ---
        if lines:
            # First line as name (fallback)
            result["name"] = lines[0].strip()

        # Try to infer from social/email
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        if email_match:
            result["email"] = email_match.group(0)
            # Use part of email as name if first line is invalid
            if not result["name"] or "@" in result["name"]:
                inferred_name = email_match.group(0).split("@")[0].replace(".", " ").title()
                result["name"] = inferred_name

        # --- Phone Number ---
        phone_match = re.search(r'(\+?\d[\d\s\-]{8,}\d)', text)
        if phone_match:
            result["mobile"] = phone_match.group(0).strip()

        # --- Degrees ---
        degree_patterns = [
            r"(Bachelor\s+of\s+[A-Za-z\s]+)",
            r"(Master\s+of\s+[A-Za-z\s]+)",
            r"(B\.?Tech|M\.?Tech|B\.?Sc|M\.?Sc|MBA|Ph\.?D)",
            r"(Bachelors?|Masters?|Doctorate) in [A-Za-z\s]+"
        ]
        degree_matches = []
        for pattern in degree_patterns:
            degree_matches += re.findall(pattern, text, flags=re.IGNORECASE)

        result["degree"] = list(set([deg.strip() for deg in degree_matches]))

        # --- Education Block ---
        education_block = re.search(
            r"(?i)(education|qualifications)[\s\S]{0,500}(?=(experience|skills|projects|$))",
            text,
            re.IGNORECASE
        )
        if education_block:
            result["education_match"] = education_block.group(0).strip()

        # --- Experience Block ---
        experience_block = re.search(
            r"(?i)(experience|employment|work history)[\s\S]{0,1000}(?=(skills|projects|certifications|$))",
            text,
            re.IGNORECASE
        )
        if experience_block:
            result["experience_match"] = experience_block.group(0).strip()

        social_patterns = [
            # r"(https?://)?(www\.)?linkedin\.com/in/[a-zA-Z0-9\-_]+",
            r"(https?://(www\.)?linkedin\.com/[a-zA-Z0-9\-_/]+)",
            r"(https?://)?(www\.)?github\.com/[a-zA-Z0-9\-_]+",
            r"(https?://)?(www\.)?twitter\.com/[a-zA-Z0-9\-_]+",
            r"(https?://)?(www\.)?facebook\.com/[a-zA-Z0-9\-_]+",
            r"(https?://)?(www\.)?stackoverflow\.com/users/\d+/[a-zA-Z0-9\-_]+"
        ]

        social_matches = ''
        for pattern in social_patterns:
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            for match in matches:
                # Reconstruct the full URL
                if isinstance(match, tuple):
                    base = ''.join(match)
                else:
                    base = match
                if not base.startswith("http"):
                    base = "https://" + base.lstrip("/")
                social_matches += base

        result["social_links"] = social_matches

        # --- Block Extraction Utility ---
        def extract_section(start_keywords, end_keywords, text):
            # Build patterns without (?i) inline flag
            start_pattern = "(" + "|".join(start_keywords) + r")[\s]*\n?"
            end_pattern = "(" + "|".join(end_keywords) + ")"
            pattern = start_pattern + r"([\s\S]{0,2000}?)" + r"(?=\n" + end_pattern + r"|\Z)"

            match = re.search(pattern, text, flags=re.IGNORECASE)
            return match.group(2).strip() if match else None

        # Extract each block (without headers)
        result["education_match"] = extract_section(
            ["education", "academic qualifications"],
            ["experience", "skills", "projects", "certifications"],
            text
        )

        result["experience_match"] = extract_section(
            ["experience", "employment", "work history"],
            ["skills", "projects", "certifications", "education"],
            text
        )

        result["skills_match"] = extract_section(
            [
                "skills", "technical skills", "professional skills", "core competencies", "areas of expertise",
                "core strengths", "proficiencies", "skill set", "relevant skills", "capabilities", "specializations",
                "knowledge areas", "expertise", "functional skills", "talents", "strengths",
                "highlights of qualifications", "domain expertise", "tools & technologies", "industry skills",
                "technical competencies" , "key competencies"
            ],
            ["projects", "certifications", "experience", "education"],
            text
        )

        result["projects_match"] = extract_section(
            ["projects", "personal projects"],
            ["certifications", "skills", "experience", "education"],
            text
        )

        result["certifications_match"] = extract_section(
            ["certifications", "licenses"],
            ["projects", "skills", "experience", "education"],
            text
        )
        # --- Experience in Years ---
        experience_years_match = re.findall(
            r"\b(\d{1,2})\s*(\+)?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)\b", text_lower
        )

        if experience_years_match:
            years_list = []
            for match in experience_years_match:
                years_list.append(int(match[0]))
                if years_list:
                    break
            if years_list:
                result["experience_in_years"] = max(years_list)
            else:
                result["experience_in_years"] = 0
        else:
            result["experience_in_years"] = 0

        return result

    def clean_string(s):
        return unicodedata.normalize('NFKD', s.strip().lower()).replace('\u200b', '').replace('\xa0', '').strip()

    def match_skills(required_skills, resume_skills, mode='exact'):
        matched = []
        if mode == 'exact':
            matched = [req for req in required_skills if req in resume_skills]
        elif mode == 'partial':
            matched = [req for req in required_skills if any(req in res for res in resume_skills)]
        elif mode == 'fuzzy':
            for req in required_skills:
                close_matches = difflib.get_close_matches(req, resume_skills, n=1, cutoff=0.8)
                if close_matches:
                    matched.append(req)
        return matched

    def compute_rating(matched_count, total_count):
        if total_count == 0:
            return '1'
        percentage = (matched_count / total_count) * 100
        if percentage >= 80:
            return '5'
        elif percentage >= 60:
            return '4'
        elif percentage >= 40:
            return '3'
        elif percentage >= 20:
            return '2'
        else:
            return '1'

    def compute_resume_ratings(self):
        for rec in self:
            try:
                resume_skills_text = (rec.skills_details or '').lower()
                resume_education_text = (rec.education_details or '').lower()
                resume_experience_text = (rec.experience_details or '').lower()

                # Extract required skills
                required_skills = [s.name.strip().lower() for s in rec.key_skills_require if s.name]
                required_education = [e.name.strip().lower() for e in rec.education_required if e.name]
                required_experience = [e.name.strip().lower() for e in rec.experience_required if e.name]

                matched_skills = [skill for skill in required_skills if skill in resume_skills_text]
                matched_education = [edu for edu in required_education if edu in resume_education_text]

                # Rating function
                def compute_rating(matched_count, total_count):
                    if total_count == 0:
                        return '1'
                    percentage = (matched_count / total_count) * 100
                    if percentage >= 80:
                        return '5'
                    elif percentage >= 60:
                        return '4'
                    elif percentage >= 40:
                        return '3'
                    elif percentage >= 20:
                        return '2'
                    else:
                        return '2'

                # Assign computed ratings
                rec.skill_rating = compute_rating(len(matched_skills), len(required_skills))
                rec.education_rating = compute_rating(len(matched_education), len(required_education))
                resume_exp = rec.experience_in_years or 0.0
                required_exp = sum([float(e.name.strip()) for e in rec.experience_required if
                                    e.name and e.name.strip().replace('.', '', 1).isdigit()])
                if required_exp == 0:
                    rec.experience_rating = '1'
                elif resume_exp >= required_exp:
                    rec.experience_rating = '5'
                else:
                    proportional_rating = max(1, round((resume_exp / required_exp) * 5))
                    rec.experience_rating = str(proportional_rating)

            except Exception as e:
                _logger.error(f"⚠ Error computing resume ratings for applicant {rec.id}: {str(e)}")
                rec.skill_rating = '1'
                rec.education_rating = '1'
                rec.experience_rating = '1'


    def action_print_offer_letter(self):
        self.ensure_one()
        return self.env.ref('recruitment_ext.action_report_offer_letter').report_action(self)

    def action_send_offer_letter_email(self):
        template = self.env.ref('recruitment_ext.mail_template_offer_letter', raise_if_not_found=False)
        if not template:
            raise UserError("Offer Letter Email Template not found.")
        for applicant in self:
            pre_onboarding_record = self.env['hr.pre.onboarding'].search([('applicant_id', '=', applicant.id),('state','=','pending')], limit=1)
            if not pre_onboarding_record:
                pre_onboarding_record = self.env['hr.pre.onboarding'].create({
                    'applicant_id': applicant.id,
                    'email':applicant.email_from,
                    'department':applicant.department_id.name,
                    'designation': applicant.job_id.name,
                    'salary':applicant.salary_package,
                    'location':applicant.office_address,
                    'date_of_joining':applicant.joining_date,
                    'state': 'pending',
                })
            ctx = {
                'default_partner_name': applicant.partner_name or '',
                'pre_onboarding_record': pre_onboarding_record.id,
                'default_position': 'Software Engineer',
                'default_joining_date': '2025-08-01',
                'default_location': 'Mumbai',
                'default_ctc': '12 LPA'
            }
            template.with_context(ctx).send_mail(applicant.id, force_send=True)

    def action_open_send_template_wizard(self):
        return {
            'name': 'Send Email Template',
            'type': 'ir.actions.act_window',
            'res_model': 'send.template.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_applicant_id': self.id,
            }
        }





# Skill Type Model
class HrSkillType(models.Model):
    _name = 'hr.skill.type'
    _description = 'Skill Type'

    name = fields.Char(string='Skill Type Name', required=True)

# Skill Model
class HrSkill(models.Model):
    _name = 'hr.skill'
    _description = 'Skill'

    name = fields.Char(string='Skill Name', required=True)
    description = fields.Text(string='Description')
    skill_type_id = fields.Many2one('hr.skill.type', string='Skill Type')

# Education Model
class HrEducation(models.Model):
    _name = 'hr.education'
    _description = 'Education Requirement'

    name = fields.Char(string='Education Level', required=True)
    description = fields.Text(string='Description')

# Experience Model
class HrExperience(models.Model):
    _name = 'hr.experience'
    _description = 'Experience Requirement'

    name = fields.Char(string='Experience Name', required=True)
    years = fields.Float(string='Years of Experience')

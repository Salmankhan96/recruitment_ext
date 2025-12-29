import requests
from odoo import models, fields, api
from odoo.exceptions import UserError

class HrJob(models.Model):
    _inherit = 'hr.job'

    naukri_posted = fields.Boolean(string="Posted on Naukri", default=False)
    naukri_response = fields.Text(string="Naukri Response", readonly=True)

    linkedin_posted = fields.Boolean(string="Posted on LinkedIn", default=False)
    linkedin_response = fields.Text(string="LinkedIn Response", readonly=True)

    indeed_posted = fields.Boolean(string="Posted on Indeed", default=False)
    indeed_response = fields.Text(string="Indeed Response", readonly=True)

    def action_post_to_naukri(self):
        for job in self:
            if job.naukri_posted:
                continue

            payload = {
                "title": job.name,
                "description": job.description or "No description",
                "location": job.address_id.city if job.address_id else "N/A",
                "experience_min": 1,
                "experience_max": 3,
                "key_skills": "Python, Odoo",
                "salary_min": 300000,
                "salary_max": 500000,
                "industry": "IT-Software",
                "functional_area": "ERP",
                "job_type": "Full Time",
                "employment_type": "Permanent",
                "company_name": "MyCompany",
            }

            headers = {
                "Authorization": "Bearer YOUR_NAUKRI_API_TOKEN",
                "Content-Type": "application/json",
            }

            try:
                response = requests.post("https://api.naukri.com/job-postings", json=payload, headers=headers)
                response.raise_for_status()
                job.naukri_posted = True
                job.naukri_response = f"✅ {response.status_code}: {response.text}"
            except requests.RequestException as e:
                job.naukri_response = f"❌ Naukri Error: {str(e)}"
                raise UserError(f"Naukri API Error: {str(e)}")

    def action_post_to_linkedin(self):
        for job in self:
            if job.linkedin_posted:
                continue

            payload = {
                "title": job.name,
                "description": job.description or "No description",
                "location": job.address_id.city if job.address_id else "N/A",
                "job_type": "FULL_TIME",
                "company_name": "MyCompany",
            }

            headers = {
                "Authorization": "Bearer YOUR_LINKEDIN_API_TOKEN",
                "Content-Type": "application/json",
            }

            try:
                response = requests.post("https://api.linkedin.com/v2/jobPosts", json=payload, headers=headers)
                response.raise_for_status()
                job.linkedin_posted = True
                job.linkedin_response = f"✅ {response.status_code}: {response.text}"
            except requests.RequestException as e:
                job.linkedin_response = f"❌ LinkedIn Error: {str(e)}"
                raise UserError(f"LinkedIn API Error: {str(e)}")

    def action_post_to_indeed(self):
        for job in self:
            if job.indeed_posted:
                continue

            payload = {
                "job_title": job.name,
                "job_description": job.description or "No description",
                "job_location": job.address_id.city if job.address_id else "N/A",
                "job_type": "Full-time",
                "company_name": "MyCompany",
            }

            headers = {
                "Authorization": "Bearer YOUR_INDEED_API_KEY",
                "Content-Type": "application/json",
            }

            try:
                response = requests.post("https://api.indeed.com/v1/jobs/post", json=payload, headers=headers)
                response.raise_for_status()
                job.indeed_posted = True
                job.indeed_response = f"✅ {response.status_code}: {response.text}"
            except requests.RequestException as e:
                job.indeed_response = f"❌ Indeed Error: {str(e)}"
                raise UserError(f"Indeed API Error: {str(e)}")




# controllers/pre_onboarding.py

from odoo import http
from odoo.http import request
import base64

class PreOnboardingController(http.Controller):

    @http.route('/pre-onboarding/<int:onboarding_id>', type='http', auth='public', website=True, csrf=False, cors='*')
    def pre_onboarding_form(self, onboarding_id, **post):
        # byte_string = request.httprequest.data
        # data = json.loads(byte_string.decode('utf-8'))

        record = request.env['hr.pre.onboarding'].sudo().browse(onboarding_id)
        if not record:
            return request.render('website.404')

        return request.render('recruitment_ext.pre_onboarding_template', {
            'record': record
        })

    @http.route('/pre-onboarding/submit', type='http', auth='public', website=True, methods=['POST'], csrf=False)
    def submit_pre_onboarding(self, **post):
        onboarding_id = post.get('onboarding_id')
        if not onboarding_id:
            return request.render('website.404', {'error_message': 'Applicant ID not found.'})

        pre_onboarding_record = request.env['hr.pre.onboarding'].sudo().browse(int(onboarding_id))
        if not pre_onboarding_record.exists():
            return request.render('website.404', {'error_message': 'Pre-onboarding record not found.'})

        update_vals = {}

        # --- Text fields ---
        text_fields = ['location']
        for field in text_fields:
            if post.get(field):
                update_vals[field] = post[field]

        # --- File uploads ---
        file_fields = [
            'acceptance_of_offer_letter', 'acceptance_of_resign_letter', 'address_proof','id_proof',
            'all_educational_certificate_with_10th_12th', 'all_merits_certificate_diploma',
            'copy_of_relieving_letter', 'duly_sign_copy_of_emp', 'fitness_certificate',
            'last_three_months_salary_slip', 'passport_size_photo', 'previous_company_form16',
            'resume_duly_sign_with_photo', 'six_month_bank_statement'
        ]

        for field in file_fields:
            uploaded_file = request.httprequest.files.get(field)
            if uploaded_file:
                uploaded_file.stream.seek(0)  # Ensure file pointer is at start
                file_content = uploaded_file.read()
                if file_content:
                    update_vals[field] = base64.b64encode(file_content).decode('ascii')

        update_vals['state'] = 'accepted'

        try:
            pre_onboarding_record.sudo().write(update_vals)
            return request.render('recruitment_ext.pre_onboarding_thanks')
        except Exception as e:
            return request.render('website.error', {'error_message': f'An error occurred: {str(e)}'})

    @http.route('/pre-onboarding/reject', type='http', auth='public', website=True)
    def reject_offer(self, id=None):
        if not id:
            return request.render('website.404', {'error_message': 'Applicant ID not provided.'})

        record = request.env['hr.pre.onboarding'].sudo().browse(int(id))
        if not record.exists():
            return request.render('website.404', {'error_message': 'Pre-onboarding record not found.'})

        # Safely update the state
        record.sudo().write({'state': 'rejected'})

        # Show a thank-you or confirmation page
        return request.render('recruitment_ext.pre_onboarding_thanks', {
            'message': 'You have successfully rejected the offer.'
        })

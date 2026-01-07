from odoo import models, fields
from odoo.tools import mute_logger
from odoo.tools.translate import html_translate


class HrJob(models.Model):
    _inherit = 'hr.job'


    ui_responsibility = fields.Char(string="Heading1")
    l1_responsibility = fields.Char(string="Body 1.1")
    l2_responsibility = fields.Char(string="Body 1.2")
    l3_responsibility = fields.Char(string="Body 1.3")
    l4_responsibility = fields.Char(string="Body 1.4")
    l5_responsibility = fields.Char(string="Body 1.5")

    ui_must_have = fields.Char(string="Heading2")
    l1_must_have = fields.Char(string="Body 2.1")
    l2_must_have = fields.Char(string="Body 2.2")
    l3_must_have = fields.Char(string="Body 2.3")
    l4_must_have = fields.Char(string="Body 2.4")
    l5_must_have = fields.Char(string="Body 2.5")

    ui_nice_to_have = fields.Char(string="Heading3")
    l1_nice_to_have = fields.Char(string="Body 3.1")
    l2_nice_to_have = fields.Char(string="Body 3.2")
    l3_nice_to_have = fields.Char(string="Body 3.3")
    l4_nice_to_have = fields.Char(string="Body 3.4")
    l5_nice_to_have = fields.Char(string="Body 3.5")

from odoo import models, fields
from odoo.tools import mute_logger
from odoo.tools.translate import html_translate


class HrJob(models.Model):
    _inherit = 'hr.job'


    ui_responsibility = fields.Char(string="Responsibility")
    l1_responsibility = fields.Char(string="Responsibility 1")
    l2_responsibility = fields.Char(string="Responsibility 2")
    l3_responsibility = fields.Char(string="Responsibility 3")
    l4_responsibility = fields.Char(string="Responsibility 4")
    l5_responsibility = fields.Char(string="Responsibility 5")

    ui_must_have = fields.Char(string="Must Have")
    l1_must_have = fields.Char(string="Must Have 1")
    l2_must_have = fields.Char(string="Must Have 2")
    l3_must_have = fields.Char(string="Must Have 3")
    l4_must_have = fields.Char(string="Must Have 4")
    l5_must_have = fields.Char(string="Must Have 5")

    ui_nice_to_have = fields.Char(string="Nice to have")
    l1_nice_to_have = fields.Char(string="Nice to have 1")
    l2_nice_to_have = fields.Char(string="Nice to have 2")
    l3_nice_to_have = fields.Char(string="Nice to have 3")
    l4_nice_to_have = fields.Char(string="Nice to have 4")
    l5_nice_to_have = fields.Char(string="Nice to have 5")
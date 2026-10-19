from odoo import fields, models


class ZenTestSideEffect(models.Model):
    _name = "zen.test.side.effect"
    _description = "Zen Test Side Effect"

    name = fields.Char(required=True, index=True)

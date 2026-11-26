from odoo import api, fields, models

INSERT_UNSAFE = "INSERT INTO zen_test_dog (name, is_admin) VALUES ('%s', FALSE)"


class ZenTestDog(models.Model):
    _name = "zen.test.dog"
    _description = "Zen Test Dog"

    name = fields.Char()
    is_admin = fields.Boolean()

    @api.model
    def create_unsafe(self, name):
        self.env.cr.execute(INSERT_UNSAFE % name)
        return True

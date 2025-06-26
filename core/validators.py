import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class SpecialCharacterValidator:
    """
    Validates that the password contains at least one special character.
    """
    def validate(self, password, user=None):
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _("This password must contain at least one special character."),
                code='password_no_special_char',
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least one special character."
        )
import re

from pydantic import BaseModel, ValidationError, field_validator, Field
from typing_extensions import Annotated, Optional
from decimal import Decimal
from aiogram.utils.i18n import gettext as _

from src.utils.helpers import escape_markdown


# Translator function for ValidationError
def translate_validation_error(error: ValidationError) -> str:
    messages = []
    for err in error.errors():
        error_type = err['type']
        if error_type == 'string_pattern_mismatch':
            message_template = escape_markdown(_("The {field} should match the pattern '{pattern}'"))
            message = message_template.format(field=err['loc'][0], pattern=err['ctx']['pattern'])
        elif error_type == 'value_error':
            message = escape_markdown(_("The {field} field has an invalid value.").format(field=err['loc'][0]))
        elif error_type == 'greater_than':
            message = escape_markdown(_("The {field} field must be greater than {limit_value}").format(
                field=err['loc'][0], limit_value=err['ctx']['gt']
            ))
        else:
            message = escape_markdown(_("Error: ") + _(err['msg']))
        messages.append(message)
    return "\n".join(messages)


VALID_TEXT_PATTERN = re.compile(r'^[\w\s.,!?\'"()\-]+$')


class AdvertisementModel(BaseModel):
    """
    Advertisement model.

    :param title: Title of the advertisement
    :param description: Description of the advertisement
    :param price: Price of the advertisement

    :raises ValidationError: If the input data is invalid

    :return: AdvertisementModel object
    """

    title: Optional[Annotated[str, Field(max_length=100)]] = None
    description: Optional[Annotated[str, Field(max_length=100)]] = None
    price: Optional[Annotated[Decimal, Field(gt=0, decimal_places=2)]] = None

    @staticmethod
    @field_validator('title')
    def title_must_be_valid(v):
        if not v.strip():
            raise ValueError(escape_markdown(_("Title cannot be empty or whitespace-only.")))
        if not AdvertisementModel.VALID_TEXT_PATTERN.match(v):
            raise ValueError(escape_markdown(_("Title contains invalid characters.")))
        return v

    @staticmethod
    @field_validator('description')
    def description_must_be_valid(v):
        if not v.strip():
            raise ValueError(escape_markdown(_("Description cannot be empty or whitespace-only.")))
        if not AdvertisementModel.VALID_TEXT_PATTERN.match(v):
            raise ValueError(escape_markdown(_("Description contains invalid characters.")))
        return v

    @staticmethod
    @field_validator('price', mode='before')
    def price_must_be_positive(v):
        if not isinstance(v, Decimal):
            raise ValueError(escape_markdown(_("Price must be a decimal.")))
        if v <= 0:
            raise ValueError(escape_markdown(_("Price must be positive.")))
        return v

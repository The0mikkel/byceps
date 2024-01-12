"""
byceps.blueprints.site.shop.order.forms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from flask_babel import lazy_gettext
from moneyed import EUR
from wtforms import SelectField, StringField
from wtforms.validators import InputRequired, Length, Optional

from byceps.services.shop.cart.models import Cart
from byceps.services.shop.order.models.order import Orderer
from byceps.services.user.models.user import User
from byceps.util.l10n import LocalizedForm


class OrderForm(LocalizedForm):
    company = StringField(lazy_gettext('Company'), validators=[Optional()])
    first_name = StringField(
        lazy_gettext('First name'), validators=[Length(min=2)]
    )
    last_name = StringField(
        lazy_gettext('Last name'), validators=[Length(min=2)]
    )
    country = StringField(
        lazy_gettext('Country'), validators=[Length(min=2, max=60)]
    )
    zip_code = StringField(
        lazy_gettext('Zip code'),
        validators=[Length(min=4, max=5)],  # DE: 5 digits, AT/CH: 4 digits
    )
    city = StringField(lazy_gettext('City'), validators=[Length(min=2)])
    street = StringField(lazy_gettext('Street'), validators=[Length(min=2)])

    def get_orderer(self, user: User) -> Orderer:
        return Orderer(
            user=user,
            company=(self.company.data or '').strip(),
            first_name=self.first_name.data.strip(),
            last_name=self.last_name.data.strip(),
            country=self.country.data.strip(),
            zip_code=self.zip_code.data.strip(),
            city=self.city.data.strip(),
            street=self.street.data.strip(),
        )


def assemble_articles_order_form(article_compilation):
    """Dynamically extend the order form with one field per article."""

    class ArticlesOrderForm(OrderForm):
        def get_field_for_article(self, article):
            name = _generate_field_name(article)
            return getattr(self, name)

        def get_cart(self, article_compilation):
            cart = Cart(EUR)
            for article, quantity in self.get_cart_items(article_compilation):
                cart.add_item(article, quantity)
            return cart

        def get_cart_items(self, article_compilation):
            for item in article_compilation:
                quantity = self.get_field_for_article(item.article).data
                if quantity > 0:
                    yield item.article, quantity

    validators = [InputRequired()]
    for item in article_compilation:
        field_name = _generate_field_name(item.article)
        choices = _create_choices(item.article)
        field = SelectField(
            lazy_gettext('Quantity'), validators, coerce=int, choices=choices
        )
        setattr(ArticlesOrderForm, field_name, field)

    return ArticlesOrderForm


def _generate_field_name(article):
    return f'article_{article.id}'


def _create_choices(article):
    max_orderable_quantity = _get_max_orderable_quantity(article)
    quantities = list(range(max_orderable_quantity + 1))
    return [(quantity, str(quantity)) for quantity in quantities]


def _get_max_orderable_quantity(article):
    return min(article.quantity, article.max_quantity_per_order)

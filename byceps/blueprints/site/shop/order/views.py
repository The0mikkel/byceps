"""
byceps.blueprints.site.shop.order.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from flask import abort, g, request
from flask_babel import gettext, format_percent
from moneyed import Currency

from byceps.blueprints.site.site.navigation import subnavigation_for_view
from byceps.services.country import country_service
from byceps.services.shop.article import article_domain_service, article_service
from byceps.services.shop.article.errors import NoArticlesAvailableError
from byceps.services.shop.article.models import ArticleCompilation
from byceps.services.shop.cart.models import Cart
from byceps.services.shop.order import order_checkout_service, order_service
from byceps.services.shop.order.email import order_email_service
from byceps.services.shop.order.models.order import Order
from byceps.services.shop.shop import shop_service
from byceps.services.shop.storefront import storefront_service
from byceps.services.user import user_service
from byceps.signals import shop as shop_signals
from byceps.util.framework.blueprint import create_blueprint
from byceps.util.framework.flash import flash_error, flash_notice, flash_success
from byceps.util.framework.templating import templated
from byceps.util.result import Err, Ok, Result
from byceps.util.views import login_required, redirect_to

from .forms import assemble_articles_order_form, OrderForm


blueprint = create_blueprint('shop_order', __name__)


@blueprint.add_app_template_filter
def tax_rate_as_percentage(tax_rate) -> str:
    # Keep a digit after the decimal point in case
    # the tax rate is a fractional number.
    return format_percent(tax_rate, '#0.0 %')


@blueprint.get('/order')
@templated
@subnavigation_for_view('shop')
def order_form(erroneous_form=None):
    """Show a form to order articles."""
    storefront = _get_storefront_or_404()
    shop = shop_service.get_shop(storefront.shop_id)

    if storefront.closed:
        flash_notice(gettext('The shop is closed.'))
        return {'article_compilation': None}

    article_compilation_result = (
        article_service.get_article_compilation_for_orderable_articles(shop.id)
    )

    match article_compilation_result:
        case Err(e):
            if isinstance(e, NoArticlesAvailableError):
                error_message = gettext('No articles are available.')
            else:
                error_message = gettext('An unknown error has occurred.')

            flash_error(error_message)
            return {'article_compilation': None}

    article_compilation = article_compilation_result.unwrap()

    if not g.user.authenticated:
        return list_articles(article_compilation)

    detail = user_service.get_detail(g.user.id)

    if erroneous_form:
        form = erroneous_form
    else:
        ArticlesOrderForm = assemble_articles_order_form(article_compilation)
        form = ArticlesOrderForm(obj=detail)

    country_names = country_service.get_country_names()

    return {
        'form': form,
        'country_names': country_names,
        'article_compilation': article_compilation,
    }


# No route registered. Intended to be called from another view function.
@templated
@subnavigation_for_view('shop')
def list_articles(article_compilation):
    """List articles for anonymous users to view."""
    return {
        'article_compilation': article_compilation,
    }


@blueprint.post('/order')
@login_required
def order():
    """Order articles."""
    storefront = _get_storefront_or_404()
    shop = shop_service.get_shop(storefront.shop_id)

    if storefront.closed:
        flash_notice(gettext('The shop is closed.'))
        return order_form()

    article_compilation_result = (
        article_service.get_article_compilation_for_orderable_articles(shop.id)
    )

    match article_compilation_result:
        case Err(e):
            if isinstance(e, NoArticlesAvailableError):
                error_message = gettext('No articles are available.')
            else:
                error_message = gettext('An unknown error has occurred.')

            flash_error(error_message)
            return order_form()

    article_compilation = article_compilation_result.unwrap()

    ArticlesOrderForm = assemble_articles_order_form(article_compilation)
    form = ArticlesOrderForm(request.form)

    if not form.validate():
        return order_form(form)

    cart = form.get_cart(article_compilation)

    if cart.is_empty():
        flash_error(gettext('No articles have been selected.'))
        return order_form(form)

    orderer = form.get_orderer(g.user)

    placement_result = _place_order(storefront, orderer, cart)
    if placement_result.is_err():
        flash_error(gettext('Placing the order has failed.'))
        return order_form(form)

    order = placement_result.unwrap()

    _flash_order_success(order)

    return redirect_to('shop_orders.view', order_id=order.id)


@blueprint.get('/order_single/<uuid:article_id>')
@login_required
@templated
@subnavigation_for_view('shop')
def order_single_form(article_id, erroneous_form=None):
    """Show a form to order a single article."""
    article = _get_article_or_404(article_id)

    storefront = _get_storefront_or_404()
    shop = shop_service.get_shop(storefront.shop_id)

    user = g.user
    detail = user_service.get_detail(user.id)

    form = erroneous_form if erroneous_form else OrderForm(obj=detail)

    if storefront.closed:
        flash_notice(gettext('The shop is closed.'))
        return {
            'form': form,
            'article': None,
        }

    article_compilation = (
        article_service.get_article_compilation_for_single_article(article.id)
    )

    country_names = country_service.get_country_names()

    if article.not_directly_orderable:
        flash_error(gettext('The article cannot be ordered directly.'))
        return {
            'form': form,
            'article': None,
        }

    if order_service.has_user_placed_orders(user.id, shop.id):
        flash_error(gettext('You cannot place another order.'))
        return {
            'form': form,
            'article': None,
        }

    if (
        article.quantity < 1
        or not article_domain_service.is_article_available_now(article)
    ):
        flash_error(gettext('The article is not available.'))
        return {
            'form': form,
            'article': None,
        }

    return {
        'form': form,
        'country_names': country_names,
        'article': article,
        'article_compilation': article_compilation,
    }


@blueprint.post('/order_single/<uuid:article_id>')
@login_required
def order_single(article_id):
    """Order a single article."""
    article = _get_article_or_404(article_id)

    storefront = _get_storefront_or_404()
    shop = shop_service.get_shop(storefront.shop_id)

    if storefront.closed:
        flash_notice(gettext('The shop is closed.'))
        return order_single_form(article.id)

    if article.not_directly_orderable:
        flash_error(gettext('The article cannot be ordered directly.'))
        return order_single_form(article.id)

    article_compilation = (
        article_service.get_article_compilation_for_single_article(article.id)
    )

    user = g.user

    if order_service.has_user_placed_orders(user.id, shop.id):
        flash_error(gettext('You cannot place another order.'))
        return order_single_form(article.id)

    if (
        article.quantity < 1
        or not article_domain_service.is_article_available_now(article)
    ):
        flash_error(gettext('The article is not available.'))
        return order_single_form(article.id)

    form = OrderForm(request.form)
    if not form.validate():
        return order_single_form(article.id, form)

    orderer = form.get_orderer(user)

    cart = _create_cart_from_article_compilation(
        shop.currency, article_compilation
    )

    placement_result = _place_order(storefront, orderer, cart)
    if placement_result.is_err():
        flash_error(gettext('Placing the order has failed.'))
        return order_form(form)

    order = placement_result.unwrap()

    _flash_order_success(order)

    return redirect_to('shop_orders.view', order_id=order.id)


def _get_storefront_or_404():
    storefront_id = g.site.storefront_id
    if storefront_id is None:
        abort(404)

    return storefront_service.get_storefront(storefront_id)


def _get_article_or_404(article_id):
    article = article_service.find_db_article(article_id)

    if article is None:
        abort(404)

    return article


def _create_cart_from_article_compilation(
    currency: Currency,
    article_compilation: ArticleCompilation,
) -> Cart:
    cart = Cart(currency)

    for item in article_compilation:
        cart.add_item(item.article, item.fixed_quantity)

    return cart


def _place_order(storefront, orderer, cart) -> Result[Order, None]:
    placement_result = order_checkout_service.place_order(
        storefront, orderer, cart
    )
    if placement_result.is_err():
        return Err(None)

    order, event = placement_result.unwrap()

    order_email_service.send_email_for_incoming_order_to_orderer(order)

    shop_signals.order_placed.send(None, event=event)

    return Ok(order)


def _flash_order_success(order):
    flash_success(
        gettext(
            'Your order <strong>%(order_number)s</strong> has been placed. '
            'Thank you!',
            order_number=order.order_number,
        ),
        text_is_safe=True,
    )

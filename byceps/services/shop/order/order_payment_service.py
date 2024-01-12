"""
byceps.services.shop.order.order_payment_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from copy import deepcopy
from datetime import datetime

from moneyed import Money
from sqlalchemy import delete, select

from byceps.database import db
from byceps.services.shop.shop.models import ShopID
from byceps.services.snippet import snippet_service
from byceps.services.snippet.errors import SnippetNotFoundError
from byceps.services.snippet.models import SnippetScope
from byceps.services.user.models.user import User
from byceps.util.l10n import format_money
from byceps.util.result import Err, Ok, Result
from byceps.util.templating import load_template

from . import order_domain_service, order_log_service
from .dbmodels.payment import DbPayment
from .models.log import OrderLogEntry
from .models.order import Order, OrderID
from .models.payment import AdditionalPaymentData, Payment


def add_payment(
    order: Order,
    created_at: datetime,
    method: str,
    amount: Money,
    initiator: User,
    additional_data: AdditionalPaymentData,
) -> Payment:
    """Add a payment to an order."""

    payment, log_entry = order_domain_service.create_payment(
        order, created_at, method, amount, initiator, additional_data
    )

    _persist_payment(payment, log_entry)

    return payment


def _persist_payment(payment: Payment, log_entry: OrderLogEntry) -> None:
    db_payment = DbPayment(
        payment.id,
        payment.order_id,
        payment.created_at,
        payment.method,
        payment.amount,
        payment.additional_data,
    )
    db.session.add(db_payment)

    db_log_entry = order_log_service.to_db_entry(log_entry)
    db.session.add(db_log_entry)

    db.session.commit()


def delete_payments_for_order(order_id: OrderID) -> None:
    """Delete all payments that belong to the order."""
    db.session.execute(delete(DbPayment).where(DbPayment.order_id == order_id))
    db.session.commit()


def get_payments_for_order(order_id: OrderID) -> list[Payment]:
    """Return the payments for that order."""
    db_payments = db.session.scalars(
        select(DbPayment).filter_by(order_id=order_id)
    ).all()

    return [_db_entity_to_payment(db_payment) for db_payment in db_payments]


def _db_entity_to_payment(db_payment: DbPayment) -> Payment:
    return Payment(
        id=db_payment.id,
        order_id=db_payment.order_id,
        created_at=db_payment.created_at,
        method=db_payment.method,
        amount=Money(db_payment.amount, db_payment.currency),
        additional_data=deepcopy(db_payment.additional_data),
    )


def create_email_payment_instructions(shop_id: ShopID, creator: User) -> None:
    """Create email payment instructions snippets for that shop in the
    supported languages.
    """
    scope = _build_shop_snippet_scope(shop_id)

    language_codes_and_bodies = [
        (
            'en',
            """
Please transfer the total amount to this bank account:

  Recipient: <name>
  IBAN: <IBAN>
  BIC: <BIC>
  Bank: <bank>
  Purpose: {{ order_number }}

We will let you know once we have received your payment.

You can view your orders here: https://www.yourparty.example/shop/orders
        """.strip(),
        ),
        (
            'de',
            """
Bitte überweise den Gesamtbetrag auf dieses Konto:

  Zahlungsempfänger: <Name>
  IBAN: <IBAN>
  BIC: <BIC>
  Bank: <Kreditinstitut>
  Verwendungszweck: {{ order_number }}

Wir werden dich informieren, sobald wir deine Zahlung erhalten haben.

Hier kannst du deine Bestellungen einsehen: https://www.yourparty.example/shop/orders
        """.strip(),
        ),
    ]

    for language_code, body in language_codes_and_bodies:
        snippet_service.create_snippet(
            scope, 'email_payment_instructions', language_code, creator, body
        )


def get_email_payment_instructions(
    order: Order, language_code: str
) -> Result[str, SnippetNotFoundError]:
    """Return the email payment instructions for that order and language."""
    scope = _build_shop_snippet_scope(order.shop_id)

    snippet_content_result = snippet_service.get_snippet_body(
        scope, 'email_payment_instructions', language_code
    )
    if snippet_content_result.is_err():
        return Err(snippet_content_result.unwrap_err())

    template = load_template(snippet_content_result.unwrap())
    rendered = template.render(
        order_id=order.id,
        order_number=order.order_number,
    )
    return Ok(rendered)


def create_html_payment_instructions(shop_id: ShopID, creator: User) -> None:
    """Create HTML payment instructions snippets for that shop in the
    supported languages.
    """
    scope = _build_shop_snippet_scope(shop_id)

    language_codes_and_bodies = [
        (
            'en',
            """
<p>Please transfer the total amount to this bank account:</p>

<table class="index" style="margin: 0 auto;">
  <tr>
    <th>Recipient</th>
    <td>&lt;name&gt;</td>
  </tr>
  <tr>
    <th>IBAN</th>
    <td>&lt;IBAN&gt;</td>
  </tr>
  <tr>
    <th>BIC</th>
    <td>&lt;BIC&gt;</td>
  </tr>
  <tr>
    <th>Bank</th>
    <td>&lt;bank&gt;</td>
  </tr>
  <tr>
    <th>Amount</th>
    <td>{{ total_amount }}</td>
  </tr>
  <tr>
    <th>Purpose</th>
    <td>{{ order_number }}</td>
  </tr>
</table>
        """.strip(),
        ),
        (
            'de',
            """
<p>Bitte überweise den Gesamtbetrag auf dieses Konto:</p>

<table class="index" style="margin: 0 auto;">
  <tr>
    <th>Zahlungsempfänger</th>
    <td>&lt;Name&gt;</td>
  </tr>
  <tr>
    <th>IBAN</th>
    <td>&lt;IBAN&gt;</td>
  </tr>
  <tr>
    <th>BIC</th>
    <td>&lt;BIC&gt;</td>
  </tr>
  <tr>
    <th>Bank</th>
    <td>&lt;Bank&gt;</td>
  </tr>
  <tr>
    <th>Betrag</th>
    <td>{{ total_amount }}</td>
  </tr>
  <tr>
    <th>Verwendungszweck</th>
    <td>{{ order_number }}</td>
  </tr>
</table>
        """.strip(),
        ),
    ]

    for language_code, body in language_codes_and_bodies:
        snippet_service.create_snippet(
            scope, 'payment_instructions', language_code, creator, body
        )


def get_html_payment_instructions(
    order: Order, language_code: str
) -> Result[str, SnippetNotFoundError]:
    """Return the HTML payment instructions for that order and language."""
    scope = _build_shop_snippet_scope(order.shop_id)

    snippet_content_result = snippet_service.get_snippet_body(
        scope, 'payment_instructions', language_code
    )
    if snippet_content_result.is_err():
        return Err(snippet_content_result.unwrap_err())

    template = load_template(snippet_content_result.unwrap())
    rendered = template.render(
        order_number=order.order_number,
        total_amount=format_money(order.total_amount),
    )
    return Ok(rendered)


def _build_shop_snippet_scope(shop_id: ShopID) -> SnippetScope:
    return SnippetScope('shop', str(shop_id))

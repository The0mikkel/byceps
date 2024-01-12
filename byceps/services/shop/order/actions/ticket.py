"""
byceps.services.shop.order.actions.ticket
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from collections.abc import Iterable
from typing import Any
from uuid import UUID

from byceps.services.shop.order import order_log_service, order_service
from byceps.services.shop.order.models.order import LineItem, Order, OrderID
from byceps.services.ticketing import (
    ticket_category_service,
    ticket_creation_service,
    ticket_revocation_service,
    ticket_service,
)
from byceps.services.ticketing.dbmodels.ticket import DbTicket
from byceps.services.ticketing.models.ticket import TicketCategoryID, TicketID
from byceps.services.user.models.user import User

from ._ticketing import create_tickets_sold_event, send_tickets_sold_event


def create_tickets(
    order: Order,
    line_item: LineItem,
    ticket_category_id: TicketCategoryID,
    initiator: User,
) -> None:
    """Create tickets."""
    owner = order.placed_by
    order_number = order.order_number
    ticket_quantity = line_item.quantity

    ticket_category = ticket_category_service.get_category(ticket_category_id)

    tickets = ticket_creation_service.create_tickets(
        ticket_category.party_id,
        ticket_category_id,
        owner,
        ticket_quantity,
        order_number=order_number,
        user=owner,
    )

    _create_creation_order_log_entries(order.id, tickets)

    data: dict[str, Any] = {
        'ticket_ids': list(sorted(str(ticket.id) for ticket in tickets))
    }
    order_service.update_line_item_processing_result(line_item.id, data)

    tickets_sold_event = create_tickets_sold_event(
        order.id, initiator, ticket_category_id, owner, ticket_quantity
    ).unwrap()
    send_tickets_sold_event(tickets_sold_event)


def _create_creation_order_log_entries(
    order_id: OrderID, tickets: Iterable[DbTicket]
) -> None:
    event_type = 'ticket-created'

    datas = [
        {
            'ticket_id': str(ticket.id),
            'ticket_code': ticket.code,
            'ticket_category_id': str(ticket.category_id),
            'ticket_owner_id': str(ticket.owned_by_id),
        }
        for ticket in tickets
    ]

    order_log_service.create_entries(event_type, order_id, datas)


def revoke_tickets(order: Order, line_item: LineItem, initiator: User) -> None:
    """Revoke all tickets related to the line item."""
    ticket_id_strs = line_item.processing_result['ticket_ids']
    ticket_ids = {
        TicketID(UUID(ticket_id_str)) for ticket_id_str in ticket_id_strs
    }
    tickets = ticket_service.get_tickets(ticket_ids)

    ticket_revocation_service.revoke_tickets(ticket_ids, initiator.id)

    _create_revocation_order_log_entries(order.id, tickets, initiator)


def _create_revocation_order_log_entries(
    order_id: OrderID, tickets: Iterable[DbTicket], initiator: User
) -> None:
    event_type = 'ticket-revoked'

    datas = [
        {
            'ticket_id': str(ticket.id),
            'ticket_code': ticket.code,
            'initiator_id': str(initiator.id),
        }
        for ticket in tickets
    ]

    order_log_service.create_entries(event_type, order_id, datas)

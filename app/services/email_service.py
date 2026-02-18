"""Email service for sending transactional emails.

Uses Flask-Mail under the hood.  All methods are safe to call even when
MAIL_USERNAME is not configured — they log a warning and return gracefully.
"""
from __future__ import annotations

import logging
from typing import Optional

from flask import current_app, render_template

logger = logging.getLogger(__name__)


def _get_mail():
    """Return the Flask-Mail instance or None if not configured."""
    mail = current_app.extensions.get("mail")
    if not mail:
        logger.warning("Flask-Mail not initialised — skipping email send")
        return None
    if not current_app.config.get("MAIL_USERNAME"):
        logger.info("MAIL_USERNAME not set — skipping email send")
        return None
    return mail


def send_email(
    to: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> bool:
    """Send a single email.

    Returns True if sent, False if skipped or failed.
    """
    mail = _get_mail()
    if not mail:
        return False

    from flask_mail import Message

    try:
        msg = Message(
            subject=subject,
            recipients=[to],
            html=html_body,
            body=text_body or "",
        )
        mail.send(msg)
        logger.info("Email sent to %s: %s", to, subject)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, e)
        return False


def send_topup_receipt(
    email: str,
    first_name: str,
    amount: float,
    utility_type: str,
    transaction_number: str,
    new_balance: float,
) -> bool:
    """Send a top-up confirmation receipt email.

    Args:
        email: Recipient email address.
        first_name: Customer's first name for personalisation.
        amount: Top-up amount in Rands.
        utility_type: e.g. 'electricity', 'water'.
        transaction_number: The transaction reference number.
        new_balance: Wallet balance after the top-up.

    Returns:
        True if sent, False otherwise.
    """
    utility_display = utility_type.replace("_", " ").title()
    subject = f"Payment Received — R{amount:.2f} {utility_display} Top-Up"

    html_body = render_template(
        "emails/topup_receipt.html",
        first_name=first_name or "Customer",
        amount=amount,
        utility_type=utility_display,
        transaction_number=transaction_number,
        new_balance=new_balance,
    )

    text_body = (
        f"Hi {first_name or 'Customer'},\n\n"
        f"Your {utility_display} wallet has been topped up with R {amount:.2f}.\n"
        f"Transaction: {transaction_number}\n"
        f"New balance: R {new_balance:.2f}\n\n"
        f"Thank you for your payment.\n"
        f"Quantify Metering"
    )

    return send_email(email, subject, html_body, text_body)

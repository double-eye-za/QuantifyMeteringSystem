"""Celery tasks for payment processing.

Handles expiry of stale pending PayFast transactions and receipt emails.
"""
from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import datetime, timedelta

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_topup_receipt_email(self, wallet_id: int, amount: float,
                              utility_type: str, transaction_number: str):
    """Send a top-up receipt email after a successful PayFast payment.

    Looks up the wallet → unit → primary tenant/owner to find the
    recipient email address and first name.

    Args:
        wallet_id: Wallet that was credited.
        amount: Top-up amount in Rands.
        utility_type: e.g. 'electricity', 'water'.
        transaction_number: Transaction reference number.
    """
    from app.models.wallet import Wallet
    from app.models.unit import Unit
    from app.services.email_service import send_topup_receipt

    wallet = Wallet.query.get(wallet_id)
    if not wallet:
        logger.warning("send_topup_receipt_email: wallet %s not found", wallet_id)
        return {"sent": False, "reason": "wallet_not_found"}

    unit = Unit.query.get(wallet.unit_id)
    if not unit:
        logger.warning("send_topup_receipt_email: unit not found for wallet %s", wallet_id)
        return {"sent": False, "reason": "unit_not_found"}

    # Find the person to email — prefer primary tenant, fallback to primary owner
    person = unit.primary_tenant or unit.primary_owner
    if not person or not person.email:
        logger.info(
            "send_topup_receipt_email: no email for wallet %s (unit %s)",
            wallet_id, unit.unit_number,
        )
        return {"sent": False, "reason": "no_email"}

    # Calculate the utility-specific balance for the receipt
    balance_field = f"{utility_type}_balance"
    new_balance = float(getattr(wallet, balance_field, wallet.balance))

    try:
        sent = send_topup_receipt(
            email=person.email,
            first_name=person.first_name,
            amount=amount,
            utility_type=utility_type,
            transaction_number=transaction_number,
            new_balance=new_balance,
        )
        if sent:
            logger.info(
                "Receipt email sent to %s for txn %s (R%.2f %s)",
                person.email, transaction_number, amount, utility_type,
            )
        return {"sent": sent, "email": person.email}
    except Exception as exc:
        logger.error("Failed to send receipt email: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=1, default_retry_delay=60)
def expire_stale_payfast_transactions(self):
    """Mark pending PayFast transactions older than 1 hour as expired.

    Runs every 30 minutes via Celery Beat.  Catches cases where the user
    abandoned the PayFast page without completing or cancelling, so the
    ITN callback was never received.
    """
    from app.db import db
    from app.models.transaction import Transaction

    cutoff = datetime.utcnow() - timedelta(hours=1)

    stale = Transaction.query.filter(
        Transaction.status == 'pending',
        Transaction.payment_gateway == 'payfast',
        Transaction.created_at < cutoff,
    ).all()

    expired_count = 0
    for txn in stale:
        txn.status = 'expired'
        txn.payment_gateway_status = 'EXPIRED'
        expired_count += 1

    if expired_count:
        db.session.commit()
        logger.info("Expired %d stale PayFast transaction(s)", expired_count)

    return {'expired': expired_count}


@shared_task(bind=True, max_retries=1, default_retry_delay=120)
def reconcile_payfast_transactions(self):
    """Daily reconciliation of PayFast transactions.

    Checks all PayFast transactions from the last 48 hours that have a
    ``payment_gateway_ref`` against the PayFast validate endpoint.

    Auto-fixes:
    - PayFast says VALID but local is pending/failed → credit wallet + complete.

    Flags:
    - PayFast says INVALID but local is completed → mismatch flagged.

    Creates an in-app Notification for admin users with the summary.
    Runs daily at midnight via Celery Beat.
    """
    import json
    from flask import current_app
    from app.db import db
    from app.models.transaction import Transaction
    from app.models.notification import Notification
    from app.utils.payfast import verify_itn_with_payfast
    from app.routes.payfast import _complete_transaction

    cutoff = datetime.utcnow() - timedelta(hours=48)
    validate_url = current_app.config.get("PAYFAST_VALIDATE_URL")
    is_sandbox = current_app.config.get("PAYFAST_SANDBOX", True)

    # In sandbox mode, PayFast validate endpoint won't work for localhost
    # transactions.  Skip server-to-server verify and just report status.
    skip_verify = is_sandbox

    # Get all PayFast transactions from the last 48 hours
    txns = Transaction.query.filter(
        Transaction.payment_gateway == "payfast",
        Transaction.created_at >= cutoff,
    ).all()

    results = {
        "total_checked": 0,
        "already_completed": 0,
        "auto_fixed": 0,
        "mismatches": 0,
        "pending_no_ref": 0,
        "errors": 0,
        "details": [],
    }

    for txn in txns:
        results["total_checked"] += 1

        # Skip transactions without a real gateway ref
        if not txn.payment_gateway_ref or txn.payment_gateway_ref in (
            "SANDBOX-MANUAL", "ADMIN-MANUAL",
        ):
            if txn.status in ("pending", "failed"):
                results["pending_no_ref"] += 1
            elif txn.status == "completed":
                results["already_completed"] += 1
            continue

        if txn.status == "completed":
            results["already_completed"] += 1
            # Optionally verify completed transactions too
            if not skip_verify and txn.payment_metadata:
                try:
                    post_data = json.loads(txn.payment_metadata)
                    if isinstance(post_data, dict):
                        is_valid = verify_itn_with_payfast(post_data, validate_url)
                        if not is_valid:
                            results["mismatches"] += 1
                            results["details"].append({
                                "txn": txn.transaction_number,
                                "issue": "completed_locally_but_payfast_invalid",
                                "amount": float(txn.amount),
                            })
                except (json.JSONDecodeError, TypeError):
                    pass
            continue

        # Pending/failed transactions with a gateway ref — verify with PayFast
        if txn.status in ("pending", "failed") and not skip_verify:
            if txn.payment_metadata:
                try:
                    post_data = json.loads(txn.payment_metadata)
                    if isinstance(post_data, dict):
                        is_valid = verify_itn_with_payfast(post_data, validate_url)
                        if is_valid:
                            # Auto-fix: PayFast says valid but we haven't completed
                            try:
                                utility_type = _complete_transaction(txn)
                                txn.payment_gateway_status = "COMPLETE"
                                txn.reconciled = True
                                txn.reconciled_at = datetime.utcnow()
                                db.session.commit()
                                results["auto_fixed"] += 1
                                results["details"].append({
                                    "txn": txn.transaction_number,
                                    "issue": "auto_fixed",
                                    "amount": float(txn.amount),
                                    "utility_type": utility_type,
                                })
                                logger.info(
                                    "Reconciliation auto-fixed txn %s (R%.2f)",
                                    txn.transaction_number, float(txn.amount),
                                )
                            except Exception as e:
                                results["errors"] += 1
                                results["details"].append({
                                    "txn": txn.transaction_number,
                                    "issue": "auto_fix_failed",
                                    "error": str(e),
                                })
                                logger.error(
                                    "Reconciliation auto-fix failed for %s: %s",
                                    txn.transaction_number, e,
                                )
                except (json.JSONDecodeError, TypeError):
                    results["errors"] += 1
        elif txn.status in ("pending", "failed"):
            results["pending_no_ref"] += 1

    # Create admin notification with summary
    summary_parts = [
        f"Checked {results['total_checked']} PayFast txn(s) (last 48h).",
    ]
    if results["auto_fixed"]:
        summary_parts.append(f"Auto-fixed {results['auto_fixed']} transaction(s).")
    if results["mismatches"]:
        summary_parts.append(f"Found {results['mismatches']} mismatch(es) — review needed.")
    if results["pending_no_ref"]:
        summary_parts.append(f"{results['pending_no_ref']} pending without PayFast reference.")
    if results["errors"]:
        summary_parts.append(f"{results['errors']} error(s) during reconciliation.")

    if results["auto_fixed"] or results["mismatches"] or results["errors"]:
        priority = "high"
    else:
        priority = "low"

    try:
        notification = Notification(
            recipient_type="system",
            recipient_id=None,
            notification_type="payfast_reconciliation",
            subject="PayFast Daily Reconciliation",
            message=" ".join(summary_parts),
            priority=priority,
            channel="in_app",
            status="sent",
            sent_at=datetime.utcnow(),
        )
        db.session.add(notification)
        db.session.commit()
    except Exception as e:
        logger.error("Failed to create reconciliation notification: %s", e)

    logger.info("PayFast reconciliation complete: %s", results)
    return results

"""
Celery tasks for notification processing.

These tasks handle:
- Scheduled checks for low credit wallets
- High usage analysis
- Real-time notification delivery
"""
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def check_low_credit_wallets(self):
    """
    Scheduled task to check all wallets for low credit.
    Runs nightly at 6 AM.

    Creates notifications for wallets below their threshold.
    """
    from ..services.notification_service import NotificationService

    logger.info("Starting low credit wallet check...")

    try:
        low_credit_wallets = NotificationService.get_wallets_below_threshold()
        notifications_created = 0

        for item in low_credit_wallets:
            wallet = item['wallet']
            threshold = item['threshold']
            is_critical = item['is_critical']

            # Skip critical ones - they're handled by check_critical_credit_wallets
            if is_critical:
                continue

            notification = NotificationService.notify_low_credit(
                wallet=wallet,
                threshold=threshold,
                is_critical=False
            )

            if notification:
                notifications_created += 1
                logger.info(
                    f"Created low credit notification for wallet {wallet.id} "
                    f"(balance: {item['balance']}, threshold: {threshold})"
                )

        logger.info(
            f"Low credit check complete. "
            f"Checked {len(low_credit_wallets)} wallets, "
            f"created {notifications_created} notifications."
        )

        return {
            'status': 'success',
            'wallets_checked': len(low_credit_wallets),
            'notifications_created': notifications_created,
        }

    except Exception as e:
        logger.error(f"Error in low credit check: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def check_critical_credit_wallets(self):
    """
    Scheduled task to check for critically low credit wallets.
    Runs every 4 hours.

    Creates urgent notifications for wallets with very low balance.
    """
    from ..services.notification_service import NotificationService

    logger.info("Starting critical credit wallet check...")

    try:
        low_credit_wallets = NotificationService.get_wallets_below_threshold()
        notifications_created = 0

        for item in low_credit_wallets:
            if not item['is_critical']:
                continue

            wallet = item['wallet']
            threshold = item['threshold']

            notification = NotificationService.notify_low_credit(
                wallet=wallet,
                threshold=threshold,
                is_critical=True
            )

            if notification:
                notifications_created += 1
                logger.warning(
                    f"Created CRITICAL credit notification for wallet {wallet.id} "
                    f"(balance: {item['balance']})"
                )

        logger.info(
            f"Critical credit check complete. "
            f"Created {notifications_created} urgent notifications."
        )

        return {
            'status': 'success',
            'notifications_created': notifications_created,
        }

    except Exception as e:
        logger.error(f"Error in critical credit check: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_high_usage(self):
    """
    Scheduled task to analyze usage patterns and detect anomalies.
    Runs nightly at 7 AM.

    Creates notifications for units with unusually high usage.
    """
    from ..services.notification_service import NotificationService
    from ..models import Meter, Wallet, Unit

    logger.info("Starting high usage analysis...")

    try:
        high_usage_items = NotificationService.get_high_usage_units(
            threshold_percentage=50.0  # Flag if 50% above average
        )
        notifications_created = 0

        for item in high_usage_items:
            meter_id = item['meter_id']
            meter = Meter.query.get(meter_id)

            if not meter or not meter.unit_id:
                continue

            # Get wallet for this unit
            wallet = Wallet.query.filter_by(unit_id=meter.unit_id).first()
            if not wallet:
                continue

            # Determine utility type from meter type
            utility_type = 'electricity'  # Default
            if meter.meter_type:
                if 'water' in meter.meter_type.lower():
                    utility_type = 'water'
                elif 'solar' in meter.meter_type.lower():
                    utility_type = 'solar'
                elif 'gas' in meter.meter_type.lower():
                    utility_type = 'gas'

            notification = NotificationService.notify_high_usage(
                wallet=wallet,
                utility_type=utility_type,
                current_usage=item['current_usage'],
                average_usage=item['average_usage'],
                percentage_increase=item['percentage_increase']
            )

            if notification:
                notifications_created += 1
                logger.info(
                    f"Created high usage notification for meter {meter_id} "
                    f"({item['percentage_increase']:.0f}% above average)"
                )

        logger.info(
            f"High usage analysis complete. "
            f"Analyzed {len(high_usage_items)} meters, "
            f"created {notifications_created} notifications."
        )

        return {
            'status': 'success',
            'meters_flagged': len(high_usage_items),
            'notifications_created': notifications_created,
        }

    except Exception as e:
        logger.error(f"Error in high usage analysis: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_topup_notification(
    self,
    wallet_id: int,
    amount: float,
    payment_method: str = None,
    utility_type: str = None
):
    """
    Real-time task to send notification after wallet top-up.

    Args:
        wallet_id: ID of the wallet that was topped up
        amount: Amount that was added
        payment_method: Method used for payment
        utility_type: Type of utility (if specific)
    """
    from ..services.notification_service import NotificationService
    from ..models import Wallet

    logger.info(f"Sending top-up notification for wallet {wallet_id}...")

    try:
        wallet = Wallet.query.get(wallet_id)
        if not wallet:
            logger.error(f"Wallet {wallet_id} not found")
            return {'status': 'error', 'message': 'Wallet not found'}

        notification = NotificationService.notify_topup_success(
            wallet=wallet,
            amount=amount,
            payment_method=payment_method,
            utility_type=utility_type
        )

        if notification:
            logger.info(f"Top-up notification created for wallet {wallet_id}")
            return {'status': 'success', 'notification_id': notification.id}
        else:
            logger.warning(f"No recipient found for wallet {wallet_id}")
            return {'status': 'skipped', 'message': 'No recipient found'}

    except Exception as e:
        logger.error(f"Error sending top-up notification: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_purchase_notification(
    self,
    wallet_id: int,
    amount: float,
    utility_type: str,
    units_purchased: float = None
):
    """
    Real-time task to send notification after utility purchase.

    Args:
        wallet_id: ID of the wallet used for purchase
        amount: Amount spent
        utility_type: Type of utility purchased
        units_purchased: Number of units purchased (optional)
    """
    from ..services.notification_service import NotificationService
    from ..models import Wallet

    logger.info(f"Sending purchase notification for wallet {wallet_id}...")

    try:
        wallet = Wallet.query.get(wallet_id)
        if not wallet:
            logger.error(f"Wallet {wallet_id} not found")
            return {'status': 'error', 'message': 'Wallet not found'}

        notification = NotificationService.notify_purchase_success(
            wallet=wallet,
            amount=amount,
            utility_type=utility_type,
            units_purchased=units_purchased
        )

        if notification:
            logger.info(f"Purchase notification created for wallet {wallet_id}")
            return {'status': 'success', 'notification_id': notification.id}
        else:
            logger.warning(f"No recipient found for wallet {wallet_id}")
            return {'status': 'skipped', 'message': 'No recipient found'}

    except Exception as e:
        logger.error(f"Error sending purchase notification: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def check_wallet_after_transaction(self, wallet_id: int):
    """
    Check wallet balance after a transaction and send low credit alert if needed.

    This is called immediately after purchases to provide real-time alerts.

    Args:
        wallet_id: ID of the wallet to check
    """
    from ..services.notification_service import NotificationService
    from ..models import Wallet

    logger.info(f"Checking wallet {wallet_id} after transaction...")

    try:
        wallet = Wallet.query.get(wallet_id)
        if not wallet:
            logger.error(f"Wallet {wallet_id} not found")
            return {'status': 'error', 'message': 'Wallet not found'}

        threshold = float(wallet.low_balance_threshold or 50.0)
        balance = float(wallet.balance or 0.0)

        if balance < threshold:
            is_critical = balance < (threshold * 0.2)

            notification = NotificationService.notify_low_credit(
                wallet=wallet,
                threshold=threshold,
                is_critical=is_critical
            )

            if notification:
                level = 'CRITICAL' if is_critical else 'LOW'
                logger.info(
                    f"{level} credit notification created for wallet {wallet_id} "
                    f"(balance: {balance}, threshold: {threshold})"
                )
                return {
                    'status': 'success',
                    'notification_id': notification.id,
                    'level': level
                }

        return {'status': 'ok', 'message': 'Balance above threshold'}

    except Exception as e:
        logger.error(f"Error checking wallet: {str(e)}")
        raise self.retry(exc=e)

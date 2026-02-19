"""
Celery tasks for prepaid meter credit control.

These tasks handle:
- Scheduled checks for zero/negative wallet balance meters
- Automatic relay disconnect for non-paying accounts (feature-flagged)
- Automatic relay reconnect when balance restored above minimum
- Audit logging of all disconnect/reconnect actions

Credit control is gated behind the 'credit_control' feature flag.
When the flag is OFF, tasks run in dry-run mode (report only, no relay commands).
When the flag is ON, tasks send relay commands via ChirpStack.

Unified wallet: All balance checks use wallet.balance (the single fund pool),
not utility-specific balances. Utility columns are cumulative spend trackers.

Architecture note: The core logic lives in plain functions (_run_disconnect,
_run_reconnect, _run_report) so it can be tested without Celery. The
@shared_task wrappers just delegate to these functions.
"""
from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import datetime

logger = get_task_logger(__name__)


# ---------------------------------------------------------------------------
# Core logic (plain functions — testable without Celery)
# ---------------------------------------------------------------------------

def _run_disconnect():
    """Core disconnect logic. Returns result dict."""
    from ..models import Meter, Unit, Wallet
    from ..services.chirpstack_service import send_relay_command
    from ..utils.feature_flags import is_feature_enabled
    from ..db import db

    credit_control_active = is_feature_enabled("credit_control")

    logger.info("=" * 60)
    logger.info("Starting zero balance meter disconnect check...")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Credit control enabled: {credit_control_active}")
    logger.info("=" * 60)

    # Find all units with electricity meters that have zero or negative wallet balance
    # Unified wallet: check main balance (the single fund pool)
    # Exclude wallets already suspended (already disconnected)
    zero_balance_units = (
        db.session.query(Unit, Wallet, Meter)
        .join(Wallet, Unit.id == Wallet.unit_id)
        .join(Meter, Unit.electricity_meter_id == Meter.id)
        .filter(
            Wallet.balance <= 0,              # Zero or negative main balance
            Wallet.is_suspended == False,     # Not already disconnected
            Meter.device_eui.isnot(None),     # Has LoRaWAN device
            Meter.is_active == True,           # Meter is active
            Unit.is_active == True,            # Unit is active
        )
        .all()
    )

    logger.info(f"Found {len(zero_balance_units)} meters with zero/negative balance (not yet suspended)")

    meters_processed = 0
    meters_disconnected = 0
    meters_failed = 0
    disconnect_details = []

    for unit, wallet, meter in zero_balance_units:
        meters_processed += 1

        detail = {
            "unit_id": unit.id,
            "unit_number": unit.unit_number,
            "meter_id": meter.id,
            "meter_serial": meter.serial_number,
            "device_eui": meter.device_eui,
            "balance": float(wallet.balance),
            "electricity_spend": float(wallet.electricity_balance),
            "timestamp": datetime.now().isoformat(),
        }

        logger.info("-" * 40)
        logger.info(f"Processing Unit {unit.unit_number}:")
        logger.info(f"  Meter: {meter.serial_number}")
        logger.info(f"  Device EUI: {meter.device_eui}")
        logger.info(f"  Wallet Balance: R{wallet.balance:.2f}")

        if credit_control_active:
            # Feature flag ON — send actual disconnect command
            try:
                device_type = meter.lorawan_device_type or "eastron_sdm"
                success, message = send_relay_command(
                    meter.device_eui, "off", device_type=device_type
                )

                if success:
                    meters_disconnected += 1
                    detail["status"] = "disconnected"
                    detail["message"] = message

                    # Mark wallet as suspended
                    wallet.is_suspended = True
                    wallet.suspension_reason = (
                        f"Auto-disconnected: wallet balance R{wallet.balance:.2f} "
                        f"at {datetime.now().isoformat()}"
                    )
                    db.session.commit()

                    logger.warning(
                        f"  DISCONNECTED: Sent relay OFF to {meter.device_eui}"
                    )
                else:
                    meters_failed += 1
                    detail["status"] = "failed"
                    detail["message"] = message
                    logger.error(
                        f"  FAILED: Could not disconnect {meter.device_eui}: {message}"
                    )
            except Exception as e:
                meters_failed += 1
                detail["status"] = "error"
                detail["message"] = str(e)
                logger.error(
                    f"  ERROR: Exception disconnecting {meter.device_eui}: {e}"
                )
        else:
            # Feature flag OFF — dry run
            detail["status"] = "dry_run"
            detail["message"] = "Disconnect command skipped (credit_control flag disabled)"
            logger.info(
                f"  DRY RUN: Would disconnect {meter.device_eui} (credit_control flag disabled)"
            )

        disconnect_details.append(detail)

    logger.info("=" * 60)
    logger.info("Zero balance disconnect check complete.")
    logger.info(f"  Credit control active: {credit_control_active}")
    logger.info(f"  Meters processed: {meters_processed}")
    logger.info(f"  Meters disconnected: {meters_disconnected}")
    logger.info(f"  Meters failed: {meters_failed}")
    logger.info("=" * 60)

    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "credit_control_active": credit_control_active,
        "meters_processed": meters_processed,
        "meters_disconnected": meters_disconnected,
        "meters_failed": meters_failed,
        "details": disconnect_details,
        "dry_run": not credit_control_active,
    }


def _run_reconnect():
    """Core reconnect logic. Returns result dict."""
    from ..models import Meter, Unit, Wallet
    from ..services.chirpstack_service import send_relay_command
    from ..utils.feature_flags import is_feature_enabled
    from ..db import db

    credit_control_active = is_feature_enabled("credit_control")

    logger.info("=" * 60)
    logger.info("Starting topped-up meter reconnection check...")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Credit control enabled: {credit_control_active}")
    logger.info("=" * 60)

    # Find suspended wallets where main balance has been restored above minimum
    # Unified wallet: check main balance, not electricity_balance
    # electricity_minimum_activation defaults to R20.00
    eligible_units = (
        db.session.query(Unit, Wallet, Meter)
        .join(Wallet, Unit.id == Wallet.unit_id)
        .join(Meter, Unit.electricity_meter_id == Meter.id)
        .filter(
            Wallet.is_suspended == True,                                    # Currently disconnected
            Wallet.balance >= Wallet.electricity_minimum_activation,        # Balance restored
            Meter.device_eui.isnot(None),                                  # Has LoRaWAN device
            Meter.is_active == True,                                       # Meter is active
            Unit.is_active == True,                                        # Unit is active
        )
        .all()
    )

    logger.info(f"Found {len(eligible_units)} suspended meters eligible for reconnection")

    meters_processed = 0
    meters_reconnected = 0
    meters_failed = 0
    reconnect_details = []

    for unit, wallet, meter in eligible_units:
        meters_processed += 1

        detail = {
            "unit_id": unit.id,
            "unit_number": unit.unit_number,
            "meter_id": meter.id,
            "meter_serial": meter.serial_number,
            "device_eui": meter.device_eui,
            "balance": float(wallet.balance),
            "minimum_activation": float(wallet.electricity_minimum_activation),
            "timestamp": datetime.now().isoformat(),
        }

        logger.info("-" * 40)
        logger.info(f"Processing Unit {unit.unit_number}:")
        logger.info(f"  Meter: {meter.serial_number}")
        logger.info(f"  Device EUI: {meter.device_eui}")
        logger.info(f"  Wallet Balance: R{wallet.balance:.2f}")
        logger.info(f"  Minimum Activation: R{wallet.electricity_minimum_activation:.2f}")

        if credit_control_active:
            # Feature flag ON — send actual reconnect command
            try:
                device_type = meter.lorawan_device_type or "eastron_sdm"
                success, message = send_relay_command(
                    meter.device_eui, "on", device_type=device_type
                )

                if success:
                    meters_reconnected += 1
                    detail["status"] = "reconnected"
                    detail["message"] = message

                    # Clear suspension
                    wallet.is_suspended = False
                    wallet.suspension_reason = None
                    db.session.commit()

                    logger.info(
                        f"  RECONNECTED: Sent relay ON to {meter.device_eui}"
                    )
                else:
                    meters_failed += 1
                    detail["status"] = "failed"
                    detail["message"] = message
                    logger.error(
                        f"  FAILED: Could not reconnect {meter.device_eui}: {message}"
                    )
            except Exception as e:
                meters_failed += 1
                detail["status"] = "error"
                detail["message"] = str(e)
                logger.error(
                    f"  ERROR: Exception reconnecting {meter.device_eui}: {e}"
                )
        else:
            # Feature flag OFF — dry run
            detail["status"] = "dry_run"
            detail["message"] = "Reconnect command skipped (credit_control flag disabled)"
            logger.info(
                f"  DRY RUN: Would reconnect {meter.device_eui} (credit_control flag disabled)"
            )

        reconnect_details.append(detail)

    logger.info("=" * 60)
    logger.info("Topped-up meter reconnection check complete.")
    logger.info(f"  Credit control active: {credit_control_active}")
    logger.info(f"  Meters processed: {meters_processed}")
    logger.info(f"  Meters reconnected: {meters_reconnected}")
    logger.info(f"  Meters failed: {meters_failed}")
    logger.info("=" * 60)

    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "credit_control_active": credit_control_active,
        "meters_processed": meters_processed,
        "meters_reconnected": meters_reconnected,
        "meters_failed": meters_failed,
        "details": reconnect_details,
        "dry_run": not credit_control_active,
    }


def _run_report():
    """Core report logic. Returns result dict."""
    from ..models import Meter, Unit, Wallet
    from ..db import db

    logger.info("Generating zero balance meters report...")

    # Unified wallet: check main balance (the single fund pool)
    zero_balance_units = (
        db.session.query(Unit, Wallet, Meter)
        .join(Wallet, Unit.id == Wallet.unit_id)
        .join(Meter, Unit.electricity_meter_id == Meter.id)
        .filter(
            Wallet.balance <= 0,
            Meter.device_eui.isnot(None),
            Meter.is_active == True,
            Unit.is_active == True,
        )
        .all()
    )

    report = []
    for unit, wallet, meter in zero_balance_units:
        report.append({
            "unit_id": unit.id,
            "unit_number": unit.unit_number,
            "estate_id": unit.estate_id,
            "meter_id": meter.id,
            "meter_serial": meter.serial_number,
            "device_eui": meter.device_eui,
            "balance": float(wallet.balance),
            "electricity_spend": float(wallet.electricity_balance),
            "water_spend": float(wallet.water_balance),
            "is_suspended": wallet.is_suspended,
        })

    logger.info(f"Report generated: {len(report)} meters with zero/negative balance")

    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "total_meters": len(report),
        "meters": report,
    }


# ---------------------------------------------------------------------------
# Celery task wrappers (thin shells that delegate to core functions)
# ---------------------------------------------------------------------------

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def disconnect_zero_balance_meters(self):
    """
    Scheduled task to disconnect electricity meters with zero or negative wallet balance.
    Runs daily at 6 AM. Gated behind 'credit_control' feature flag.
    """
    try:
        return _run_disconnect()
    except Exception as e:
        logger.error(f"Error in zero balance disconnect check: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def reconnect_topped_up_meters(self):
    """
    Scheduled task to reconnect meters where wallet balance restored above minimum.
    Runs every 30 min. Gated behind 'credit_control' feature flag.
    """
    try:
        return _run_reconnect()
    except Exception as e:
        logger.error(f"Error in topped-up meter reconnection check: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def get_zero_balance_meters_report(self):
    """
    Generate a report of all meters with zero or negative wallet balance.
    Does NOT disconnect - just reports for review.
    """
    try:
        return _run_report()
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise self.retry(exc=e)

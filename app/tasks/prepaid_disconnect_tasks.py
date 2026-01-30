"""
Celery tasks for prepaid meter disconnect functionality.

These tasks handle:
- Scheduled checks for zero/negative credit electricity meters
- Automatic relay disconnect for non-paying accounts
- Audit logging of disconnect actions

IMPORTANT: The actual disconnect functionality is currently COMMENTED OUT
for safety during development. Uncomment when payment integration is complete
and ready for production.
"""
from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import datetime

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def disconnect_zero_balance_meters(self):
    """
    Scheduled task to disconnect electricity meters with zero or negative credit.
    Runs daily at 6 AM.

    This task:
    1. Finds all electricity meters linked to units with zero/negative wallet balance
    2. Filters for meters that have device_eui (LoRaWAN controllable)
    3. Sends relay OFF command to disconnect power
    4. Logs all actions for audit trail

    Returns:
        dict: Summary of meters checked and disconnected
    """
    from ..models import Meter, Unit, Wallet
    from ..services.chirpstack_service import send_relay_command
    from ..db import db

    logger.info("=" * 60)
    logger.info("Starting zero balance meter disconnect check...")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    try:
        # Find all units with electricity meters that have zero or negative balance
        # Join: Unit -> Wallet (for balance) and Unit -> Meter (for device_eui)
        zero_balance_units = (
            db.session.query(Unit, Wallet, Meter)
            .join(Wallet, Unit.id == Wallet.unit_id)
            .join(Meter, Unit.electricity_meter_id == Meter.id)
            .filter(
                Wallet.electricity_balance <= 0,  # Zero or negative balance
                Meter.device_eui.isnot(None),     # Has LoRaWAN device
                Meter.is_active == True,          # Meter is active
                Unit.is_active == True,           # Unit is active
            )
            .all()
        )

        logger.info(f"Found {len(zero_balance_units)} meters with zero/negative balance")

        meters_processed = 0
        meters_disconnected = 0
        meters_failed = 0
        disconnect_details = []

        for unit, wallet, meter in zero_balance_units:
            meters_processed += 1

            detail = {
                'unit_id': unit.id,
                'unit_number': unit.unit_number,
                'meter_id': meter.id,
                'meter_serial': meter.serial_number,
                'device_eui': meter.device_eui,
                'electricity_balance': float(wallet.electricity_balance),
                'timestamp': datetime.now().isoformat(),
            }

            logger.info("-" * 40)
            logger.info(f"Processing Unit {unit.unit_number}:")
            logger.info(f"  Meter: {meter.serial_number}")
            logger.info(f"  Device EUI: {meter.device_eui}")
            logger.info(f"  Electricity Balance: R{wallet.electricity_balance:.2f}")

            # ============================================================
            # SAFETY: Disconnect command is COMMENTED OUT
            # Uncomment the code below when ready for production
            # ============================================================

            # TODO: Uncomment when payment integration is complete
            # try:
            #     success, message = send_relay_command(meter.device_eui, "off")
            #
            #     if success:
            #         meters_disconnected += 1
            #         detail['status'] = 'disconnected'
            #         detail['message'] = message
            #         logger.warning(
            #             f"  DISCONNECTED: Sent relay OFF to {meter.device_eui}"
            #         )
            #     else:
            #         meters_failed += 1
            #         detail['status'] = 'failed'
            #         detail['message'] = message
            #         logger.error(
            #             f"  FAILED: Could not disconnect {meter.device_eui}: {message}"
            #         )
            # except Exception as e:
            #     meters_failed += 1
            #     detail['status'] = 'error'
            #     detail['message'] = str(e)
            #     logger.error(
            #         f"  ERROR: Exception disconnecting {meter.device_eui}: {e}"
            #     )

            # For now, just log what WOULD happen (dry run)
            detail['status'] = 'dry_run'
            detail['message'] = 'Disconnect command skipped (safety mode)'
            logger.info(
                f"  DRY RUN: Would disconnect {meter.device_eui} (command disabled)"
            )

            disconnect_details.append(detail)

        logger.info("=" * 60)
        logger.info("Zero balance disconnect check complete.")
        logger.info(f"  Meters processed: {meters_processed}")
        logger.info(f"  Meters disconnected: {meters_disconnected}")
        logger.info(f"  Meters failed: {meters_failed}")
        logger.info("=" * 60)

        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'meters_processed': meters_processed,
            'meters_disconnected': meters_disconnected,
            'meters_failed': meters_failed,
            'details': disconnect_details,
            'dry_run': True,  # Change to False when disconnect is enabled
        }

    except Exception as e:
        logger.error(f"Error in zero balance disconnect check: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def get_zero_balance_meters_report(self):
    """
    Generate a report of all meters with zero or negative balance.
    Does NOT disconnect - just reports for review.

    Returns:
        dict: List of meters that would be disconnected
    """
    from ..models import Meter, Unit, Wallet
    from ..db import db

    logger.info("Generating zero balance meters report...")

    try:
        zero_balance_units = (
            db.session.query(Unit, Wallet, Meter)
            .join(Wallet, Unit.id == Wallet.unit_id)
            .join(Meter, Unit.electricity_meter_id == Meter.id)
            .filter(
                Wallet.electricity_balance <= 0,
                Meter.device_eui.isnot(None),
                Meter.is_active == True,
                Unit.is_active == True,
            )
            .all()
        )

        report = []
        for unit, wallet, meter in zero_balance_units:
            report.append({
                'unit_id': unit.id,
                'unit_number': unit.unit_number,
                'estate_id': unit.estate_id,
                'meter_id': meter.id,
                'meter_serial': meter.serial_number,
                'device_eui': meter.device_eui,
                'electricity_balance': float(wallet.electricity_balance),
                'total_balance': float(wallet.balance),
            })

        logger.info(f"Report generated: {len(report)} meters with zero/negative balance")

        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'total_meters': len(report),
            'meters': report,
        }

    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise self.retry(exc=e)

"""
Celery tasks for meter communication health monitoring.

These tasks handle:
- Periodic checks for meters that have stopped communicating
- Creating MeterAlert records for offline meters
- Sending in-app notifications to system admins
"""
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def check_meter_communication_health(self):
    """
    Scheduled task to detect meters that have stopped communicating.
    Runs every 15 minutes via Celery beat.

    For each active meter with an expected_posting_interval configured:
    1. Check if time since last_communication exceeds the interval
    2. If offline and not already flagged:
       - Set communication_status = 'offline'
       - Create MeterAlert (communication_loss)
       - Create in-app Notification for system admins
    """
    return _run_meter_communication_health()


def _run_meter_communication_health():
    """
    Core logic extracted for testability (Celery task proxies can't be called
    directly in tests — see MEMORY.md).
    """
    from datetime import datetime

    from ..db import db
    from ..models import Meter, MeterAlert, Notification

    logger.info("Starting meter communication health check...")

    try:
        now = datetime.utcnow()

        # Query active meters that have a posting interval configured
        meters = (
            Meter.query
            .filter(
                Meter.is_active == True,
                Meter.expected_posting_interval.isnot(None),
                Meter.last_communication.isnot(None),
            )
            .all()
        )

        meters_checked = 0
        meters_offline = 0
        alerts_created = 0

        for meter in meters:
            meters_checked += 1

            seconds_since_last = (now - meter.last_communication).total_seconds()

            if seconds_since_last <= meter.expected_posting_interval:
                continue  # Meter is communicating within expected window

            # Meter has exceeded its expected posting interval
            if meter.communication_status == 'offline':
                # Already flagged — don't create duplicate alerts
                continue

            # ── Mark offline ──
            meter.communication_status = 'offline'
            meters_offline += 1

            # ── Check for existing unresolved alert ──
            existing_alert = MeterAlert.query.filter_by(
                meter_id=meter.id,
                alert_type='communication_loss',
                is_resolved=False,
            ).first()

            if existing_alert:
                logger.debug(
                    f"Meter {meter.serial_number} already has unresolved "
                    f"communication_loss alert (ID={existing_alert.id})"
                )
                continue

            # ── Create MeterAlert ──
            hours = int(seconds_since_last // 3600)
            minutes = int((seconds_since_last % 3600) // 60)
            interval_display = _format_interval(meter.expected_posting_interval)

            alert_message = (
                f"Meter {meter.serial_number} ({meter.lorawan_device_type or meter.meter_type}) "
                f"has not reported in {hours}h {minutes}m. "
                f"Expected interval: {interval_display}. "
                f"Last communication: {meter.last_communication.strftime('%Y-%m-%d %H:%M:%S')} UTC."
            )

            alert = MeterAlert(
                meter_id=meter.id,
                alert_type='communication_loss',
                severity='warning',
                message=alert_message,
            )
            db.session.add(alert)
            alerts_created += 1

            # ── Create in-app Notification for system admins ──
            notification = Notification(
                recipient_type='system',
                recipient_id=0,  # System-wide notification
                notification_type='meter_alert',
                subject=f'Meter Offline: {meter.serial_number}',
                message=alert_message,
                channel='in_app',
                priority='high',
                status='sent',
                sent_at=now,
            )
            db.session.add(notification)

            logger.warning(
                f"Meter {meter.serial_number} marked OFFLINE — "
                f"last seen {hours}h {minutes}m ago "
                f"(expected every {interval_display})"
            )

        db.session.commit()

        logger.info(
            f"Meter health check complete. "
            f"Checked {meters_checked} meters, "
            f"{meters_offline} newly offline, "
            f"{alerts_created} alerts created."
        )

        return {
            'status': 'success',
            'meters_checked': meters_checked,
            'meters_offline': meters_offline,
            'alerts_created': alerts_created,
        }

    except Exception as e:
        logger.error(f"Error in meter health check: {str(e)}", exc_info=True)
        db.session.rollback()
        raise


def _format_interval(seconds):
    """Format seconds into a human-readable interval string."""
    if seconds >= 86400:
        hours = seconds / 3600
        return f"{hours:.0f}h"
    elif seconds >= 3600:
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        if mins:
            return f"{hours}h {mins}m"
        return f"{hours}h"
    elif seconds >= 60:
        return f"{seconds // 60}m"
    else:
        return f"{seconds}s"

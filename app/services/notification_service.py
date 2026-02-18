"""
Notification service for creating and managing notifications.

This service handles:
- Creating notifications for various events
- Low credit warnings
- Purchase confirmations
- Top-up confirmations
- High usage alerts
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, List
from decimal import Decimal

from ..db import db
from ..models import Notification, Wallet, Person, Unit, Transaction, MeterReading


class NotificationService:
    """Service for managing notifications."""

    # Notification types
    TYPE_LOW_CREDIT = 'low_credit'
    TYPE_CRITICAL_CREDIT = 'critical_credit'
    TYPE_TOPUP_SUCCESS = 'topup_success'
    TYPE_PURCHASE_SUCCESS = 'purchase_success'
    TYPE_HIGH_USAGE = 'high_usage'
    TYPE_METER_READING = 'meter_reading'
    TYPE_MAINTENANCE = 'maintenance'
    TYPE_SOLAR_REPORT = 'solar_report'

    @staticmethod
    def create_notification(
        recipient_id: int,
        notification_type: str,
        subject: str,
        message: str,
        recipient_type: str = 'resident',
        channel: str = 'in_app',
        priority: str = 'normal',
        metadata: Optional[dict] = None
    ) -> Notification:
        """
        Create a new notification.

        Args:
            recipient_id: ID of the person/user receiving the notification
            notification_type: Type of notification (low_credit, topup_success, etc.)
            subject: Short subject/title for the notification
            message: Full notification message
            recipient_type: Type of recipient ('resident', 'user', 'system')
            channel: Delivery channel ('in_app', 'email', 'sms', 'push')
            priority: Priority level ('low', 'normal', 'high', 'urgent')
            metadata: Optional additional data as dict

        Returns:
            Created Notification object
        """
        notification = Notification(
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            notification_type=notification_type,
            subject=subject,
            message=message,
            channel=channel,
            priority=priority,
            status='sent',
            sent_at=datetime.utcnow(),
        )

        db.session.add(notification)
        db.session.commit()

        return notification

    @classmethod
    def notify_low_credit(
        cls,
        wallet: Wallet,
        threshold: float,
        is_critical: bool = False
    ) -> Optional[Notification]:
        """
        Create a low credit notification for a wallet owner.

        Args:
            wallet: The wallet with low credit
            threshold: The threshold that triggered the alert
            is_critical: Whether this is a critical (very low) alert

        Returns:
            Created notification or None if no recipient found
        """
        # Get the person associated with this unit
        unit = Unit.query.get(wallet.unit_id)
        if not unit:
            return None

        # Find resident/owner for this unit
        person_id = None

        # Check unit ownerships
        if unit.ownerships:
            for ownership in unit.ownerships:
                if ownership.person_id:
                    person_id = ownership.person_id
                    break

        # Check unit tenancies if no owner found
        if not person_id and unit.tenancies:
            for tenancy in unit.tenancies:
                if tenancy.person_id:
                    person_id = tenancy.person_id
                    break

        if not person_id:
            return None

        # Check if we already sent this notification today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        notification_type = cls.TYPE_CRITICAL_CREDIT if is_critical else cls.TYPE_LOW_CREDIT

        existing = Notification.query.filter(
            Notification.recipient_id == person_id,
            Notification.notification_type == notification_type,
            Notification.created_at >= today_start,
        ).first()

        if existing:
            return None  # Already notified today

        # Create notification
        balance = float(wallet.balance) if wallet.balance else 0.0

        if is_critical:
            subject = 'Critical Credit Warning'
            message = (
                f'Your wallet balance is critically low at R {balance:.2f}. '
                f'Please top up immediately to avoid service interruption.'
            )
            priority = 'urgent'
        else:
            subject = 'Low Credit Warning'
            message = (
                f'Your wallet balance (R {balance:.2f}) has fallen below '
                f'your alert threshold of R {threshold:.2f}. '
                f'Consider topping up soon to ensure uninterrupted service.'
            )
            priority = 'high'

        return cls.create_notification(
            recipient_id=person_id,
            notification_type=notification_type,
            subject=subject,
            message=message,
            priority=priority,
        )

    @classmethod
    def notify_topup_success(
        cls,
        wallet: Wallet,
        amount: float,
        payment_method: Optional[str] = None,
        utility_type: Optional[str] = None
    ) -> Optional[Notification]:
        """
        Create a notification for successful wallet top-up.

        Args:
            wallet: The wallet that was topped up
            amount: Amount that was added
            payment_method: Method used for payment
            utility_type: Type of utility (electricity, water, etc.)

        Returns:
            Created notification or None if no recipient found
        """
        person_id = cls._get_wallet_person_id(wallet)
        if not person_id:
            return None

        # Format message
        method_display = {
            'card': 'card payment',
            'eft': 'EFT transfer',
            'instant_eft': 'instant EFT',
            'cash': 'cash payment',
            'manual_admin': 'admin credit'
        }.get(payment_method, 'payment')

        if utility_type:
            utility_display = utility_type.replace('_', ' ').title()
            message = (
                f'Your {utility_display} wallet has been topped up with R {amount:.2f} '
                f'via {method_display}. New balance: R {float(wallet.balance):.2f}.'
            )
        else:
            message = (
                f'Your wallet has been topped up with R {amount:.2f} via {method_display}. '
                f'New balance: R {float(wallet.balance):.2f}.'
            )

        return cls.create_notification(
            recipient_id=person_id,
            notification_type=cls.TYPE_TOPUP_SUCCESS,
            subject='Wallet Top-Up Successful',
            message=message,
            priority='normal',
        )

    @classmethod
    def notify_purchase_success(
        cls,
        wallet: Wallet,
        amount: float,
        utility_type: str,
        units_purchased: Optional[float] = None
    ) -> Optional[Notification]:
        """
        Create a notification for successful utility purchase.

        Args:
            wallet: The wallet used for purchase
            amount: Amount spent
            utility_type: Type of utility purchased
            units_purchased: Number of units purchased (kWh, kL, etc.)

        Returns:
            Created notification or None if no recipient found
        """
        person_id = cls._get_wallet_person_id(wallet)
        if not person_id:
            return None

        utility_display = utility_type.replace('_', ' ').title()

        if units_purchased:
            unit_label = 'kWh' if utility_type == 'electricity' else 'kL'
            message = (
                f'You have successfully purchased {units_purchased:.2f} {unit_label} '
                f'of {utility_display} for R {amount:.2f}. '
                f'Remaining balance: R {float(wallet.balance):.2f}.'
            )
        else:
            message = (
                f'You have successfully purchased R {amount:.2f} of {utility_display} credit. '
                f'Remaining balance: R {float(wallet.balance):.2f}.'
            )

        return cls.create_notification(
            recipient_id=person_id,
            notification_type=cls.TYPE_PURCHASE_SUCCESS,
            subject=f'{utility_display} Purchase Successful',
            message=message,
            priority='normal',
        )

    @classmethod
    def notify_high_usage(
        cls,
        wallet: Wallet,
        utility_type: str,
        current_usage: float,
        average_usage: float,
        percentage_increase: float
    ) -> Optional[Notification]:
        """
        Create a notification for high utility usage.

        Args:
            wallet: The wallet associated with the unit
            utility_type: Type of utility with high usage
            current_usage: Current period usage
            average_usage: Average usage
            percentage_increase: Percentage above average

        Returns:
            Created notification or None if no recipient found
        """
        person_id = cls._get_wallet_person_id(wallet)
        if not person_id:
            return None

        # Check if we already sent this notification today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        existing = Notification.query.filter(
            Notification.recipient_id == person_id,
            Notification.notification_type == cls.TYPE_HIGH_USAGE,
            Notification.created_at >= today_start,
        ).first()

        if existing:
            return None

        utility_display = utility_type.replace('_', ' ').title()
        unit_label = 'kWh' if utility_type == 'electricity' else 'kL'

        message = (
            f'Your {utility_display} usage is {percentage_increase:.0f}% higher than usual. '
            f'Current: {current_usage:.2f} {unit_label}, '
            f'Average: {average_usage:.2f} {unit_label}. '
            f'Please check for any issues or leaks.'
        )

        return cls.create_notification(
            recipient_id=person_id,
            notification_type=cls.TYPE_HIGH_USAGE,
            subject=f'High {utility_display} Usage Alert',
            message=message,
            priority='high',
        )

    @classmethod
    def _get_wallet_person_id(cls, wallet: Wallet) -> Optional[int]:
        """Get the person ID associated with a wallet's unit."""
        unit = Unit.query.get(wallet.unit_id)
        if not unit:
            return None

        # Check unit ownerships
        if unit.ownerships:
            for ownership in unit.ownerships:
                if ownership.person_id:
                    return ownership.person_id

        # Check unit tenancies
        if unit.tenancies:
            for tenancy in unit.tenancies:
                if tenancy.person_id:
                    return tenancy.person_id

        return None

    @classmethod
    def get_wallets_below_threshold(cls) -> List[dict]:
        """
        Get all wallets with balance below their alert threshold.

        Returns:
            List of dicts with wallet info and threshold status
        """
        results = []

        wallets = Wallet.query.filter(Wallet.status == 'active').all()

        for wallet in wallets:
            threshold = float(wallet.low_balance_threshold or 50.0)
            balance = float(wallet.balance or 0.0)

            if balance < threshold:
                # Determine if critical (less than 20% of threshold)
                is_critical = balance < (threshold * 0.2)

                results.append({
                    'wallet': wallet,
                    'balance': balance,
                    'threshold': threshold,
                    'is_critical': is_critical,
                })

        return results

    @classmethod
    def get_high_usage_units(cls, threshold_percentage: float = 50.0) -> List[dict]:
        """
        Get units with usage significantly above their average.

        Args:
            threshold_percentage: Percentage above average to flag as high usage

        Returns:
            List of dicts with unit info and usage details
        """
        results = []

        # Get readings from the last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        month_ago = datetime.utcnow() - timedelta(days=30)

        # This is a simplified version - in production you'd want more sophisticated
        # usage analysis based on meter readings

        from sqlalchemy import func

        # Get recent readings grouped by meter
        recent_readings = db.session.query(
            MeterReading.meter_id,
            func.sum(MeterReading.reading_value).label('total_reading')
        ).filter(
            MeterReading.reading_date >= week_ago
        ).group_by(MeterReading.meter_id).all()

        # Get historical average for comparison
        for meter_id, current_total in recent_readings:
            historical = db.session.query(
                func.avg(MeterReading.reading_value)
            ).filter(
                MeterReading.meter_id == meter_id,
                MeterReading.reading_date >= month_ago,
                MeterReading.reading_date < week_ago
            ).scalar()

            if historical and current_total:
                # Calculate percentage increase
                avg_weekly = float(historical) * 7  # Rough weekly average
                if avg_weekly > 0:
                    percentage = ((float(current_total) - avg_weekly) / avg_weekly) * 100
                    if percentage > threshold_percentage:
                        results.append({
                            'meter_id': meter_id,
                            'current_usage': float(current_total),
                            'average_usage': avg_weekly,
                            'percentage_increase': percentage,
                        })

        return results

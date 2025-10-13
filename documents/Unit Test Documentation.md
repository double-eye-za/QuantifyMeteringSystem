# Unit Test Documentation
## Quantify Metering System - Phase 1

---

**Document Information**
- **Version**: 1.0
- **Date**: October 2025
- **Test Framework**: pytest
- **Coverage Target**: 80% minimum
- **Stack**: Python 3.9+, Flask 3.0+, PostgreSQL, SQLAlchemy 2.0+

---

## Table of Contents

1. [Test Strategy](#test-strategy)
2. [Test Structure](#test-structure)
3. [Unit Tests](#unit-tests)
4. [Integration Tests](#integration-tests)
5. [Test Data & Fixtures](#test-data--fixtures)
6. [Test Coverage](#test-coverage)
7. [CI/CD Integration](#cicd-integration)

---

## Test Strategy

### Testing Pyramid
```
         /\
        /  \  E2E Tests (5%)
       /    \ 
      /------\ Integration Tests (25%)
     /        \
    /----------\ Unit Tests (70%)
```

### Test Categories
1. **Unit Tests**: Individual functions and methods
2. **Integration Tests**: API endpoints and database operations
3. **Performance Tests**: Load and stress testing
4. **Security Tests**: Authentication and authorization

### Testing Principles
- Test behavior, not implementation
- Each test should be independent
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Mock external dependencies
- Test edge cases and error conditions

---

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Global fixtures
├── unit/                       # Unit tests
│   ├── __init__.py
│   ├── models/
│   │   ├── test_estate.py
│   │   ├── test_unit.py
│   │   ├── test_meter.py
│   │   ├── test_wallet.py
│   │   ├── test_transaction.py
│   │   └── test_rate_table.py
│   ├── services/
│   │   ├── test_wallet_service.py
│   │   ├── test_meter_service.py
│   │   ├── test_billing_service.py
│   │   ├── test_alert_service.py
│   │   └── test_rate_calculation.py
│   └── utils/
│       ├── test_validators.py
│       └── test_calculations.py
├── integration/                # Integration tests
│   ├── __init__.py
│   ├── api/
│   │   ├── test_auth.py
│   │   ├── test_estates_api.py
│   │   ├── test_units_api.py
│   │   ├── test_wallets_api.py
│   │   ├── test_meters_api.py
│   │   └── test_reports_api.py
│   └── database/
│       ├── test_repositories.py
│       └── test_transactions.py
├── fixtures/                   # Test data
│   ├── __init__.py
│   ├── estates.py
│   ├── units.py
│   ├── meters.py
│   └── transactions.py
└── performance/               # Performance tests
    ├── __init__.py
    └── test_load.py
```

---

## Unit Tests

### 1. Model Tests

#### test_estate.py
```python
import pytest
from datetime import datetime
from app.models import Estate, Unit
from app.exceptions import ValidationError

class TestEstateModel:
    """Test Estate model functionality"""
    
    def test_estate_creation(self, db_session):
        """Test creating a new estate"""
        estate = Estate(
            code="TEST001",
            name="Test Estate",
            total_units=50,
            contact_email="test@estate.com"
        )
        db_session.add(estate)
        db_session.commit()
        
        assert estate.id is not None
        assert estate.code == "TEST001"
        assert estate.total_units == 50
        assert estate.is_active is True
    
    def test_estate_unique_code(self, db_session, sample_estate):
        """Test estate code uniqueness constraint"""
        duplicate = Estate(
            code=sample_estate.code,
            name="Another Estate",
            total_units=30
        )
        db_session.add(duplicate)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_estate_relationships(self, db_session, estate_with_units):
        """Test estate-unit relationships"""
        assert len(estate_with_units.units) == 10
        assert all(unit.estate_id == estate_with_units.id 
                  for unit in estate_with_units.units)
    
    def test_estate_soft_delete(self, db_session, sample_estate):
        """Test soft delete functionality"""
        sample_estate.is_active = False
        sample_estate.deleted_at = datetime.utcnow()
        db_session.commit()
        
        # Should still exist in database
        assert Estate.query.get(sample_estate.id) is not None
        # But not in active query
        active = Estate.query.filter_by(is_active=True).all()
        assert sample_estate not in active
    
    def test_estate_markup_validation(self):
        """Test markup percentage validation"""
        estate = Estate(
            code="TEST002",
            name="Test Estate",
            electricity_markup_percentage=150  # Invalid
        )
        
        with pytest.raises(ValidationError) as exc:
            estate.validate()
        assert "markup_percentage must be between 0 and 100" in str(exc.value)
```

#### test_wallet.py
```python
import pytest
from decimal import Decimal
from app.models import Wallet
from app.exceptions import InsufficientBalanceError

class TestWalletModel:
    """Test Wallet model functionality"""
    
    def test_wallet_creation(self, db_session, sample_unit):
        """Test creating a wallet for a unit"""
        wallet = Wallet(
            unit_id=sample_unit.id,
            balance=Decimal("500.00"),
            electricity_balance=Decimal("200.00"),
            water_balance=Decimal("150.00"),
            solar_balance=Decimal("150.00")
        )
        db_session.add(wallet)
        db_session.commit()
        
        assert wallet.id is not None
        assert wallet.balance == Decimal("500.00")
        assert wallet.low_balance_threshold == Decimal("50.00")  # Default
    
    def test_wallet_balance_constraint(self, db_session, sample_unit):
        """Test wallet balance constraints"""
        wallet = Wallet(
            unit_id=sample_unit.id,
            balance=Decimal("100.00"),
            electricity_balance=Decimal("60.00"),
            water_balance=Decimal("50.00"),  # Total exceeds balance
            solar_balance=Decimal("0.00")
        )
        
        with pytest.raises(ValidationError) as exc:
            wallet.validate()
        assert "utility balances cannot exceed total balance" in str(exc.value)
    
    def test_electricity_minimum_activation(self, sample_wallet):
        """Test electricity activation minimum"""
        sample_wallet.electricity_balance = Decimal("10.00")
        sample_wallet.electricity_minimum_activation = Decimal("20.00")
        
        assert not sample_wallet.can_activate_electricity()
        
        sample_wallet.electricity_balance = Decimal("25.00")
        assert sample_wallet.can_activate_electricity()
    
    def test_water_debt_allowed(self, sample_wallet):
        """Test water can go negative (debt)"""
        sample_wallet.water_balance = Decimal("-50.00")
        sample_wallet.validate()  # Should not raise
        
        assert sample_wallet.has_water_debt()
        assert sample_wallet.water_debt_amount() == Decimal("50.00")
    
    def test_low_balance_alert_fixed(self, sample_wallet):
        """Test fixed amount low balance alert"""
        sample_wallet.balance = Decimal("45.00")
        sample_wallet.low_balance_threshold = Decimal("50.00")
        sample_wallet.low_balance_alert_type = "fixed"
        
        assert sample_wallet.is_low_balance()
    
    def test_low_balance_alert_days(self, sample_wallet):
        """Test days remaining low balance alert"""
        sample_wallet.balance = Decimal("100.00")
        sample_wallet.daily_avg_consumption = Decimal("30.00")
        sample_wallet.low_balance_alert_type = "days_remaining"
        sample_wallet.low_balance_days_threshold = 5
        
        # 100/30 = 3.33 days < 5 days threshold
        assert sample_wallet.is_low_balance()
        assert sample_wallet.days_remaining() == 3
```

### 2. Service Tests

#### test_wallet_service.py
```python
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from app.services import WalletService
from app.exceptions import (
    InsufficientBalanceError, 
    MinimumActivationError,
    WalletSuspendedError
)

class TestWalletService:
    """Test Wallet service business logic"""
    
    @pytest.fixture
    def wallet_service(self, db_session):
        return WalletService(db_session)
    
    def test_topup_success(self, wallet_service, sample_wallet):
        """Test successful wallet top-up"""
        initial_balance = sample_wallet.balance
        
        transaction = wallet_service.topup(
            wallet_id=sample_wallet.id,
            amount=Decimal("500.00"),
            payment_method="eft",
            reference="EFT123456"
        )
        
        assert sample_wallet.balance == initial_balance + Decimal("500.00")
        assert transaction.transaction_type == "topup"
        assert transaction.status == "completed"
    
    def test_topup_invalid_amount(self, wallet_service, sample_wallet):
        """Test top-up with invalid amount"""
        with pytest.raises(ValidationError) as exc:
            wallet_service.topup(
                wallet_id=sample_wallet.id,
                amount=Decimal("-100.00"),
                payment_method="eft"
            )
        assert "Amount must be positive" in str(exc.value)
    
    def test_purchase_electricity_success(self, wallet_service, sample_wallet):
        """Test successful electricity purchase"""
        sample_wallet.balance = Decimal("100.00")
        sample_wallet.electricity_minimum_activation = Decimal("20.00")
        
        transaction = wallet_service.purchase_electricity(
            wallet_id=sample_wallet.id,
            amount=Decimal("50.00")
        )
        
        assert sample_wallet.balance == Decimal("50.00")
        assert sample_wallet.electricity_balance == Decimal("50.00")
        assert transaction.meter_activated is True
    
    def test_purchase_electricity_insufficient_balance(
        self, wallet_service, sample_wallet
    ):
        """Test electricity purchase with insufficient balance"""
        sample_wallet.balance = Decimal("30.00")
        
        with pytest.raises(InsufficientBalanceError) as exc:
            wallet_service.purchase_electricity(
                wallet_id=sample_wallet.id,
                amount=Decimal("50.00")
            )
        assert "Insufficient balance" in str(exc.value)
    
    def test_purchase_electricity_below_minimum(
        self, wallet_service, sample_wallet
    ):
        """Test electricity purchase below activation minimum"""
        sample_wallet.balance = Decimal("100.00")
        sample_wallet.electricity_balance = Decimal("0.00")
        sample_wallet.electricity_minimum_activation = Decimal("20.00")
        
        transaction = wallet_service.purchase_electricity(
            wallet_id=sample_wallet.id,
            amount=Decimal("10.00")  # Below minimum
        )
        
        assert transaction.meter_activated is False
        assert transaction.activation_minimum_met is False
    
    def test_purchase_water_allows_debt(self, wallet_service, sample_wallet):
        """Test water purchase allows negative balance"""
        sample_wallet.balance = Decimal("10.00")
        sample_wallet.water_balance = Decimal("5.00")
        
        # Purchase more than available
        transaction = wallet_service.purchase_water(
            wallet_id=sample_wallet.id,
            amount=Decimal("20.00")
        )
        
        assert sample_wallet.water_balance == Decimal("-5.00")  # Debt
        assert transaction.transaction_type == "purchase_water"
    
    @patch('app.services.wallet_service.send_notification')
    def test_low_balance_notification(
        self, mock_notification, wallet_service, sample_wallet
    ):
        """Test low balance notification is sent"""
        sample_wallet.balance = Decimal("30.00")
        sample_wallet.low_balance_threshold = Decimal("50.00")
        
        wallet_service.check_and_send_alerts(sample_wallet.id)
        
        mock_notification.assert_called_once()
        call_args = mock_notification.call_args[1]
        assert call_args['notification_type'] == 'low_balance'
        assert sample_wallet.id in str(call_args['message'])
```

#### test_rate_calculation.py
```python
import pytest
from decimal import Decimal
from datetime import datetime, time
from app.services import RateCalculationService
from app.models import RateTable, RateTableTier

class TestRateCalculation:
    """Test rate calculation logic"""
    
    @pytest.fixture
    def calc_service(self):
        return RateCalculationService()
    
    def test_tiered_rate_calculation(self, calc_service, tiered_rate_table):
        """Test tiered block rate calculation"""
        # Tiers: 0-50 @ R1.50, 51-200 @ R2.00, 201+ @ R2.50
        
        # Within first tier
        cost = calc_service.calculate_tiered_cost(
            tiered_rate_table, 
            consumption=30
        )
        assert cost == Decimal("45.00")  # 30 * 1.50
        
        # Across two tiers
        cost = calc_service.calculate_tiered_cost(
            tiered_rate_table,
            consumption=100
        )
        # 50 * 1.50 + 50 * 2.00 = 75 + 100 = 175
        assert cost == Decimal("175.00")
        
        # All three tiers
        cost = calc_service.calculate_tiered_cost(
            tiered_rate_table,
            consumption=250
        )
        # 50 * 1.50 + 150 * 2.00 + 50 * 2.50 = 75 + 300 + 125 = 500
        assert cost == Decimal("500.00")
    
    def test_time_of_use_calculation(self, calc_service, tou_rate_table):
        """Test time-of-use rate calculation"""
        # Peak: 06:00-09:00, 17:00-20:00 @ R3.00
        # Standard: 09:00-17:00 @ R2.00
        # Off-peak: 20:00-06:00 @ R1.50
        
        # Peak time
        peak_time = datetime(2025, 1, 15, 18, 0)  # 6 PM
        cost = calc_service.calculate_tou_cost(
            tou_rate_table,
            consumption=10,
            timestamp=peak_time
        )
        assert cost == Decimal("30.00")  # 10 * 3.00
        
        # Off-peak time
        offpeak_time = datetime(2025, 1, 15, 22, 0)  # 10 PM
        cost = calc_service.calculate_tou_cost(
            tou_rate_table,
            consumption=10,
            timestamp=offpeak_time
        )
        assert cost == Decimal("15.00")  # 10 * 1.50
    
    def test_markup_application(self, calc_service):
        """Test markup percentage application"""
        base_cost = Decimal("100.00")
        markup_percentage = Decimal("20.00")
        
        total = calc_service.apply_markup(base_cost, markup_percentage)
        assert total == Decimal("120.00")
    
    def test_solar_free_allocation(self, calc_service):
        """Test solar free allocation calculation"""
        consumption = Decimal("75.00")  # kWh
        free_allocation = Decimal("50.00")  # kWh
        rate = Decimal("2.00")  # per kWh
        
        cost = calc_service.calculate_solar_cost(
            consumption, free_allocation, rate
        )
        # Only charge for excess: (75 - 50) * 2.00 = 50
        assert cost == Decimal("50.00")
        
        # Within free allocation
        cost = calc_service.calculate_solar_cost(
            Decimal("30.00"), free_allocation, rate
        )
        assert cost == Decimal("0.00")
```

### 3. Alert Service Tests

#### test_alert_service.py
```python
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch
from app.services import AlertService

class TestAlertService:
    """Test alert generation and delivery logic"""
    
    @pytest.fixture
    def alert_service(self, db_session):
        return AlertService(db_session)
    
    def test_should_send_fixed_alert(self, alert_service, sample_wallet):
        """Test fixed amount alert trigger"""
        sample_wallet.balance = Decimal("45.00")
        sample_wallet.low_balance_threshold = Decimal("50.00")
        sample_wallet.low_balance_alert_type = "fixed"
        sample_wallet.last_low_balance_alert = None
        
        assert alert_service.should_send_alert(sample_wallet) is True
        
        # Above threshold
        sample_wallet.balance = Decimal("55.00")
        assert alert_service.should_send_alert(sample_wallet) is False
    
    def test_should_send_days_alert(self, alert_service, sample_wallet):
        """Test days remaining alert trigger"""
        sample_wallet.balance = Decimal("60.00")
        sample_wallet.daily_avg_consumption = Decimal("25.00")
        sample_wallet.low_balance_alert_type = "days_remaining"
        sample_wallet.low_balance_days_threshold = 3
        
        # 60/25 = 2.4 days < 3 days threshold
        assert alert_service.should_send_alert(sample_wallet) is True
    
    def test_alert_frequency_limiting(self, alert_service, sample_wallet):
        """Test alert frequency limiting"""
        sample_wallet.balance = Decimal("30.00")
        sample_wallet.low_balance_threshold = Decimal("50.00")
        sample_wallet.alert_frequency_hours = 24
        sample_wallet.last_low_balance_alert = datetime.utcnow() - timedelta(hours=12)
        
        # Last alert was 12 hours ago, frequency is 24 hours
        assert alert_service.should_send_alert(sample_wallet) is False
        
        # Last alert was 25 hours ago
        sample_wallet.last_low_balance_alert = datetime.utcnow() - timedelta(hours=25)
        assert alert_service.should_send_alert(sample_wallet) is True
    
    def test_smart_alert_calculation(self, alert_service, sample_wallet):
        """Test smart alert based on consumption trends"""
        consumption_history = [
            Decimal("20.00"),  # 7 days ago
            Decimal("22.00"),
            Decimal("24.00"),
            Decimal("26.00"),
            Decimal("28.00"),
            Decimal("30.00"),
            Decimal("32.00"),  # Yesterday
        ]
        
        trend = alert_service.calculate_consumption_trend(consumption_history)
        assert trend == "increasing"
        
        # Calculate recommended alert threshold
        threshold = alert_service.calculate_smart_threshold(
            consumption_history,
            target_days=5
        )
        # Average ~26, increasing trend, 5 days = ~130+buffer
        assert threshold >= Decimal("130.00")
```

---

## Integration Tests

### 1. API Endpoint Tests

#### test_estates_api.py
```python
import pytest
import json
from base64 import b64encode

class TestEstatesAPI:
    """Test estate API endpoints"""
    
    @pytest.fixture
    def auth_headers(self):
        credentials = b64encode(b"admin:password").decode('ascii')
        return {"Authorization": f"Basic {credentials}"}
    
    def test_list_estates(self, client, auth_headers, sample_estates):
        """Test GET /api/v1/estates"""
        response = client.get('/api/v1/estates', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json
        assert 'data' in data
        assert len(data['data']) == len(sample_estates)
        assert 'page' in data
        assert 'total' in data
    
    def test_list_estates_pagination(self, client, auth_headers, many_estates):
        """Test estate list pagination"""
        response = client.get(
            '/api/v1/estates?page=2&per_page=10',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['page'] == 2
        assert data['per_page'] == 10
        assert len(data['data']) <= 10
    
    def test_get_estate_detail(self, client, auth_headers, sample_estate):
        """Test GET /api/v1/estates/{id}"""
        response = client.get(
            f'/api/v1/estates/{sample_estate.id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json['data']
        assert data['id'] == str(sample_estate.id)
        assert data['code'] == sample_estate.code
        assert 'units_summary' in data
        assert 'meters_summary' in data
        assert 'wallet_summary' in data
    
    def test_create_estate(self, client, auth_headers):
        """Test POST /api/v1/estates"""
        estate_data = {
            "code": "NEW001",
            "name": "New Estate",
            "total_units": 75,
            "contact_name": "Manager Name",
            "contact_email": "manager@estate.com",
            "electricity_markup_percentage": 15.00
        }
        
        response = client.post(
            '/api/v1/estates',
            headers=auth_headers,
            data=json.dumps(estate_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = response.json['data']
        assert data['code'] == "NEW001"
        assert data['electricity_markup_percentage'] == 15.00
    
    def test_create_estate_duplicate_code(
        self, client, auth_headers, sample_estate
    ):
        """Test creating estate with duplicate code"""
        estate_data = {
            "code": sample_estate.code,
            "name": "Another Estate"
        }
        
        response = client.post(
            '/api/v1/estates',
            headers=auth_headers,
            data=json.dumps(estate_data),
            content_type='application/json'
        )
        
        assert response.status_code == 409
        assert "already exists" in response.json['error']
    
    def test_update_estate(self, client, auth_headers, sample_estate):
        """Test PUT /api/v1/estates/{id}"""
        update_data = {
            "contact_email": "newemail@estate.com",
            "electricity_markup_percentage": 25.00
        }
        
        response = client.put(
            f'/api/v1/estates/{sample_estate.id}',
            headers=auth_headers,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json['data']
        assert data['contact_email'] == "newemail@estate.com"
        assert data['electricity_markup_percentage'] == 25.00
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to API"""
        response = client.get('/api/v1/estates')
        assert response.status_code == 401
```

#### test_wallets_api.py
```python
class TestWalletsAPI:
    """Test wallet API endpoints"""
    
    def test_get_wallet_details(self, client, auth_headers, sample_wallet):
        """Test GET /api/v1/wallets/{id}"""
        response = client.get(
            f'/api/v1/wallets/{sample_wallet.id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json['data']
        assert 'balance' in data
        assert 'alert_config' in data
        assert 'activation_minimums' in data
        assert data['alert_config']['low_balance_threshold'] == 50.00
    
    def test_topup_wallet(self, client, auth_headers, sample_wallet):
        """Test POST /api/v1/wallets/{id}/topup"""
        initial_balance = float(sample_wallet.balance)
        
        topup_data = {
            "amount": 500.00,
            "payment_method": "eft",
            "reference": "TEST123"
        }
        
        response = client.post(
            f'/api/v1/wallets/{sample_wallet.id}/topup',
            headers=auth_headers,
            data=json.dumps(topup_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json['data']
        assert data['balance_after'] == initial_balance + 500.00
        assert data['transaction_type'] == 'topup'
    
    def test_purchase_electricity(self, client, auth_headers, sample_wallet):
        """Test POST /api/v1/wallets/{id}/purchase"""
        sample_wallet.balance = Decimal("100.00")
        
        purchase_data = {
            "utility_type": "electricity",
            "amount": 50.00
        }
        
        response = client.post(
            f'/api/v1/wallets/{sample_wallet.id}/purchase',
            headers=auth_headers,
            data=json.dumps(purchase_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json['data']
        assert data['electricity_credit_added'] == 50.00
        assert 'meter_activated' in data
        assert 'activation_minimum_met' in data
    
    def test_update_alert_config(self, client, auth_headers, sample_wallet):
        """Test PUT /api/v1/wallets/{id}/alert-config"""
        config_data = {
            "low_balance_threshold": 75.00,
            "alert_type": "days",
            "days_threshold": 5,
            "smart_alerts_enabled": True
        }
        
        response = client.put(
            f'/api/v1/wallets/{sample_wallet.id}/alert-config',
            headers=auth_headers,
            data=json.dumps(config_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        # Verify changes
        wallet = Wallet.query.get(sample_wallet.id)
        assert wallet.low_balance_threshold == Decimal("75.00")
        assert wallet.low_balance_alert_type == "days"
```

---

## Test Data & Fixtures

### conftest.py
```python
import pytest
import os
from decimal import Decimal
from datetime import datetime, timedelta
from app import create_app
from app.core.database import Base, get_engine, SessionLocal
from tests.fixtures import *

@pytest.fixture(scope='session')
def app():
    """Create test application"""
    os.environ["ENV"] = "test"
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/quantify_test"
    
    app = create_app()
    app.config['TESTING'] = True
    
    # Create tables
    Base.metadata.create_all(bind=get_engine())
    
    yield app
    
    # Cleanup
    Base.metadata.drop_all(bind=get_engine())

@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture(scope='function')
def db_session():
    """Create clean database session for each test"""
    session = SessionLocal()
    
    # Begin nested transaction
    session.begin_nested()
    
    yield session
    
    # Rollback to clean state
    session.rollback()
    session.close()

@pytest.fixture
def sample_estate(db_session):
    """Create sample estate"""
    estate = Estate(
        code="TEST001",
        name="Test Estate",
        total_units=50,
        contact_email="test@estate.com",
        electricity_markup_percentage=Decimal("20.00"),
        solar_free_allocation_kwh=Decimal("50.00")
    )
    db_session.add(estate)
    db_session.commit()
    return estate

@pytest.fixture
def sample_unit(db_session, sample_estate):
    """Create sample unit"""
    unit = Unit(
        estate_id=sample_estate.id,
        unit_number="A-101",
        floor="Ground",
        occupancy_status="occupied"
    )
    db_session.add(unit)
    db_session.commit()
    return unit

@pytest.fixture
def sample_wallet(db_session, sample_unit):
    """Create sample wallet with balance"""
    wallet = Wallet(
        unit_id=sample_unit.id,
        balance=Decimal("500.00"),
        electricity_balance=Decimal("200.00"),
        water_balance=Decimal("150.00"),
        solar_balance=Decimal("150.00"),
        low_balance_threshold=Decimal("50.00"),
        electricity_minimum_activation=Decimal("20.00"),
        water_minimum_activation=Decimal("20.00")
    )
    db_session.add(wallet)
    db_session.commit()
    return wallet

@pytest.fixture
def tiered_rate_table(db_session):
    """Create tiered rate table"""
    rate_table = RateTable(
        name="Residential Tiered",
        utility_type="electricity",
        rate_structure={
            "type": "tiered",
            "tiers": [
                {"from_kwh": 0, "to_kwh": 50, "rate": 1.50},
                {"from_kwh": 51, "to_kwh": 200, "rate": 2.00},
                {"from_kwh": 201, "to_kwh": None, "rate": 2.50}
            ]
        },
        effective_from=datetime.utcnow().date()
    )
    db_session.add(rate_table)
    db_session.commit()
    return rate_table
```

---

## Test Coverage

### Coverage Configuration (pytest.ini)
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --cov=app
    --cov-report=html
    --cov-report=term
    --cov-fail-under=80
    --maxfail=1
    --strict-markers
markers =
    slow: marks tests as slow
    integration: integration tests
    unit: unit tests
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/models/test_wallet.py

# Run specific test
pytest tests/unit/models/test_wallet.py::TestWalletModel::test_wallet_creation

# Run by marker
pytest -m unit
pytest -m integration

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x

# Run parallel (requires pytest-xdist)
pytest -n 4
```

### Coverage Report Example
```
----------- coverage: platform darwin, python 3.9.0 -----------
Name                                  Stmts   Miss  Cover
---------------------------------------------------------
app/__init__.py                          12      0   100%
app/api/v1/__init__.py                    8      0   100%
app/api/v1/auth/dependencies.py         25      2    92%
app/api/v1/estates/endpoints.py         85      5    94%
app/api/v1/wallets/endpoints.py         92      3    97%
app/core/config.py                      15      0   100%
app/core/database.py                    22      0   100%
app/models/estate.py                    45      2    96%
app/models/wallet.py                     68      4    94%
app/services/wallet_service.py         125      8    94%
app/services/alert_service.py           78      5    94%
app/services/rate_calculation.py        95      3    97%
---------------------------------------------------------
TOTAL                                   670     32    95%

Required test coverage of 80% reached. Total coverage: 95.22%
```

---

## CI/CD Integration

### GitHub Actions (.github/workflows/test.yml)
```yaml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: quantify_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python 3.9
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        flake8 app tests
        black --check app tests
        mypy app
    
    - name: Run tests with coverage
      env:
        DATABASE_URL: postgresql://test:test@localhost/quantify_test
      run: |
        pytest --cov=app --cov-report=xml --cov-report=term
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
    
    - name: Generate coverage badge
      if: github.ref == 'refs/heads/main'
      run: |
        coverage-badge -o coverage.svg
    
    - name: Archive test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: |
          htmlcov/
          coverage.xml
```

---

## Best Practices

### 1. Test Naming
```python
# Good
def test_wallet_topup_with_valid_amount_increases_balance():
def test_electricity_purchase_below_minimum_does_not_activate_meter():

# Bad
def test_wallet():
def test_1():
```

### 2. Test Isolation
```python
# Good - Each test is independent
def test_create_estate(db_session):
    estate = create_estate()  # Creates its own test data
    
# Bad - Tests depend on each other
def test_1_create_estate(db_session):
    global estate
    estate = create_estate()

def test_2_update_estate(db_session):
    update_estate(estate)  # Depends on test_1
```

### 3. Assertions
```python
# Good - Specific assertions
assert wallet.balance == Decimal("100.00")
assert transaction.status == "completed"

# Bad - Generic assertions
assert wallet
assert transaction
```

### 4. Mock External Dependencies
```python
# Good
@patch('app.services.payment_gateway.process_payment')
def test_payment(mock_payment):
    mock_payment.return_value = {"status": "success"}
    
# Bad - Calling real external service
def test_payment():
    result = payment_gateway.process_payment()  # Real API call
```

---

## Document Version History

- v1.0 - Initial unit test documentation for Phase 1

---

*End of Unit Test Documentation*
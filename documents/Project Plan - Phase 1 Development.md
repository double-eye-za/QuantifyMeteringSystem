# Project Plan - Phase 1 Development
## Quantify Metering System - Backend Implementation

---

**Document Information**
- **Version**: 1.0
- **Date**: October 2025
- **Phase**: Phase 1 - Core Backend Development
- **Methodology**: Agile/Sprint-based with AI-assisted development
- **Duration**: 6-8 weeks
- **Stack**: Python 3.9+, Flask 3.0+, PostgreSQL, SQLAlchemy 2.0+

---

## Executive Summary

This project plan outlines the development of Phase 1 backend systems for the Quantify Metering System. The phase focuses on establishing the database infrastructure, developing RESTful APIs, and implementing comprehensive unit testing. Meter integration will be deferred to Phase 2.

### Phase 1 Scope
- Complete database implementation
- Core API endpoints for admin portal
- Comprehensive unit testing
- Basic authentication and security
- Development and staging environments

### Out of Scope (Phase 2)
- Physical meter integration (E460, DC450)
- Real-time meter data collection
- Mobile app APIs with push notifications
- Payment gateway integration (EFT, Credit/Debit cards)
- SMS notifications for critical alerts
- Push notifications for mobile app (low balance, disconnection, etc.)

---

## Development Approach

### AI-Assisted Development Strategy

1. **Code Generation**
   - Use AI for boilerplate code generation
   - SQLAlchemy model generation from schema
   - API endpoint scaffolding
   - Test case generation

2. **Code Review**
   - AI-assisted code review for best practices
   - Security vulnerability scanning
   - Performance optimization suggestions
   - Documentation generation

3. **Testing**
   - Automated test case generation
   - Edge case identification
   - Test data generation
   - Coverage analysis

---

## Project Timeline

### Overall Schedule (6-8 weeks)

| Phase | Duration | Weeks |
|-------|----------|-------|
| Sprint 0: Setup & Planning | 1 week | Week 1 |
| Sprint 1: Database Implementation | 2 weeks | Weeks 2-3 |
| Sprint 2: Core API Development | 2 weeks | Weeks 4-5 |
| Sprint 3: Extended APIs & Testing | 2 weeks | Weeks 6-7 |
| Sprint 4: Integration & Deployment | 1 week | Week 8 |

---

## Sprint 0: Project Setup & Planning (Week 1)

### Objectives
- Set up development environment
- Initialize project structure
- Configure development tools
- Establish CI/CD pipeline

### Tasks

#### Day 1-2: Environment Setup
- [ ] Install Python 3.9+, PostgreSQL, Redis
- [ ] Set up virtual environment
- [ ] Configure VS Code/PyCharm with AI assistants
- [ ] Install development tools (Black, Flake8, pytest)
- [ ] Create project repository

#### Day 3-4: Project Structure
```bash
quantify-metering/
├── src/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── auth/
│   │   │       ├── estates/
│   │   │       ├── units/
│   │   │       ├── meters/
│   │   │       ├── wallets/
│   │   │       ├── rates/
│   │   │       └── reports/
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   └── exceptions.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   └── [model files]
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── [service files]
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── [utility files]
│   └── wsgi.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── migrations/
├── scripts/
├── docs/
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── Makefile
└── README.md
```

#### Day 5: Configuration & Documentation
- [ ] Create `.env.example` with all config variables
- [ ] Set up logging configuration
- [ ] Create Makefile for common commands
- [ ] Write initial README.md
- [ ] Set up GitHub Actions for CI/CD

### Deliverables
- Configured development environment
- Project structure created
- CI/CD pipeline configured
- Development guidelines documented

---

## Sprint 1: Database Implementation (Weeks 2-3)

### Objectives
- Implement complete database schema
- Create SQLAlchemy models
- Set up migrations
- Implement data validation

### Week 2: Core Database Setup

#### Day 1-2: Database Configuration
```python
# src/app/core/config.py
from pydantic import BaseSettings, PostgresDsn

class Settings(BaseSettings):
    ENV: str = "development"
    DEBUG: bool = True
    PROJECT_NAME: str = "Quantify Metering System"
    VERSION: str = "1.0.0"
    
    DATABASE_URL: PostgresDsn
    TEST_DATABASE_URL: PostgresDsn | None = None
    
    BASIC_AUTH_REALM: str = "Quantify Admin"
    SECRET_KEY: str
    
    # Database
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_PRE_PING: bool = True
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

#### Day 3-4: Base Models & Mixins
```python
# src/app/models/base.py
from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class TimestampMixin:
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class AuditMixin(TimestampMixin):
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))

class SoftDeleteMixin:
    deleted_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
```

#### Day 5: Core Entity Models
- [ ] User model with password hashing
- [ ] Role model with permissions
- [ ] Estate model with relationships
- [ ] Unit model with validations

### Week 3: Extended Models & Migrations

#### Day 1-2: Financial Models
- [ ] Wallet model with balance constraints
- [ ] Transaction model with audit trail
- [ ] Rate table models (tiered, TOU, seasonal)
- [ ] Payment method configurations

#### Day 3-4: Meter Models
- [ ] Meter registry model
- [ ] Meter readings model
- [ ] Meter alerts model
- [ ] Mock meter data generator (for testing)

#### Day 5: Migrations & Seeds
```bash
# Create migrations
alembic init migrations
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head

# Seed data script
python scripts/seed_data.py
```

### AI Tasks for Sprint 1
1. **Model Generation**
   ```prompt
   Generate SQLAlchemy model for [table_name] based on this schema:
   [paste table definition]
   Include proper relationships, validations, and indexes.
   ```

2. **Validation Rules**
   ```prompt
   Create Pydantic validators for the Wallet model ensuring:
   - Balance cannot be negative for electricity
   - Water balance can go negative
   - Total balance equals sum of utility balances
   ```

3. **Test Data Generation**
   ```prompt
   Generate realistic test data for:
   - 2 estates with 50 units each
   - Residents with South African details
   - Transaction history for last 3 months
   ```

### Deliverables
- Complete database schema implemented
- All SQLAlchemy models created
- Migration scripts ready
- Seed data for development
- Database documentation updated

---

## Sprint 2: Core API Development (Weeks 4-5)

### Objectives
- Implement authentication system
- Develop core CRUD APIs
- Implement business logic
- Add request validation

### Week 4: Foundation & Authentication

#### Day 1-2: Flask Application Setup
```python
# src/app/__init__.py
from flask import Flask
from flask_cors import CORS
from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import api_v1_blueprint

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    
    # Extensions
    CORS(app)
    init_db(app)
    
    # Blueprints
    app.register_blueprint(api_v1_blueprint, url_prefix='/api/v1')
    
    # Error handlers
    register_error_handlers(app)
    
    return app
```

#### Day 3-4: Authentication Implementation
```python
# src/app/api/v1/auth/dependencies.py
from functools import wraps
from flask import request, abort
from werkzeug.security import check_password_hash
from app.services.user_service import UserService

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth:
            abort(401, "Authentication required")
        
        user = UserService.authenticate(auth.username, auth.password)
        if not user:
            abort(401, "Invalid credentials")
        
        request.current_user = user
        return f(*args, **kwargs)
    return decorated_function

def require_role(role):
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            if request.current_user.role.name != role:
                abort(403, "Insufficient permissions")
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

#### Day 5: Repository Pattern
```python
# src/app/repositories/base.py
from typing import Generic, TypeVar, Optional, List
from sqlalchemy.orm import Session
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def get(self, id: UUID) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def list(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, **kwargs) -> ModelType:
        db_obj = self.model(**kwargs)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(self, id: UUID, **kwargs) -> Optional[ModelType]:
        db_obj = self.get(id)
        if db_obj:
            for key, value in kwargs.items():
                setattr(db_obj, key, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: UUID) -> bool:
        db_obj = self.get(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False
```

### Week 5: API Endpoints

#### Day 1: Estate Management APIs
- [ ] GET /estates (list with pagination)
- [ ] GET /estates/{id} (detail with stats)
- [ ] POST /estates (create)
- [ ] PUT /estates/{id} (update)
- [ ] DELETE /estates/{id} (soft delete)

#### Day 2: Unit Management APIs
- [ ] GET /units (list with filters)
- [ ] GET /units/{id} (detail with meters)
- [ ] POST /units (create with validation)
- [ ] PUT /units/{id} (update)
- [ ] POST /units/{id}/assign-resident

#### Day 3: Wallet & Transaction APIs
- [ ] GET /wallets/{id} (balance and history)
- [ ] POST /wallets/{id}/topup (add credit)
- [ ] POST /wallets/{id}/purchase (buy utility)
- [ ] GET /transactions (list with filters)
- [ ] POST /transactions/{id}/reverse (admin only)

#### Day 4: Rate Table APIs
- [ ] GET /rate-tables (list)
- [ ] POST /rate-tables (create with validation)
- [ ] POST /rate-tables/{id}/calculate (test calculation)
- [ ] PUT /rate-tables/{id} (update)
- [ ] POST /estates/{id}/assign-rates

#### Day 5: Meter APIs (Mock Data) & Notification Foundation
- [ ] GET /meters (list all meters)
- [ ] GET /meters/{id}/readings (mock readings)
- [ ] POST /meters/{id}/readings (manual entry)
- [ ] GET /meters/{id}/status (mock status)
- [ ] Notification queue infrastructure (prepare for Phase 2 push notifications)
- [ ] Notification templates and storage structure

### AI Tasks for Sprint 2
1. **API Endpoint Generation**
   ```prompt
   Generate Flask blueprint for Estate CRUD operations:
   - Include pagination using the ListQuery schema
   - Add proper error handling
   - Include request validation with Pydantic
   - Follow RESTful conventions
   ```

2. **Business Logic Implementation**
   ```prompt
   Implement the wallet top-up logic:
   - Validate amount > 0
   - Create transaction record
   - Update wallet balance atomically
   - Return updated balance
   - Handle concurrent updates
   ```

3. **Error Handler Generation**
   ```prompt
   Create comprehensive error handlers for:
   - ValidationError (422)
   - NotFound (404)
   - Unauthorized (401)
   - BusinessLogicError (400)
   Include proper logging and user-friendly messages
   ```

### Deliverables
- Authentication system working
- Core CRUD APIs implemented
- Business logic for wallets
- Request/response validation
- API documentation updated

---

## Sprint 3: Extended APIs & Testing (Weeks 6-7)

### Objectives
- Complete remaining APIs
- Implement comprehensive testing
- Add performance optimizations
- Create integration tests

### Week 6: Advanced Features

#### Day 1-2: Reporting APIs
```python
# src/app/api/v1/reports/endpoints.py
@reports_bp.route('/estate-consumption', methods=['GET'])
@require_auth
def estate_consumption_report():
    """Generate estate consumption report"""
    query = ReportQuery(**request.args)
    service = ReportService(db.session)
    data = service.estate_consumption(
        estate_id=query.estate_id,
        start_date=query.start_date,
        end_date=query.end_date,
        utility_type=query.utility_type
    )
    return jsonify(data)

@reports_bp.route('/reconciliation', methods=['GET'])
@require_auth
def reconciliation_report():
    """Bulk meter vs unit meters reconciliation"""
    # Implementation
    pass

@reports_bp.route('/low-credit', methods=['GET'])
@require_auth
def low_credit_report():
    """Units with low credit balances"""
    # Implementation
    pass
```

#### Day 3-4: Batch Operations
```python
# src/app/api/v1/batch/endpoints.py
@batch_bp.route('/batch', methods=['POST'])
@require_auth
def batch_operations():
    """Execute multiple operations in transaction"""
    operations = request.json.get('operations', [])
    results = []
    
    with db.session.begin():
        for op in operations:
            result = execute_operation(op)
            results.append(result)
    
    return jsonify({"results": results})
```

#### Day 5: Search & Filtering
- [ ] Implement full-text search
- [ ] Add advanced filtering options
- [ ] Create search indexes
- [ ] Optimize query performance

### Week 7: Comprehensive Testing

#### Day 1-2: Unit Tests
```python
# tests/unit/test_wallet_service.py
import pytest
from app.services.wallet_service import WalletService
from app.models import Wallet, Transaction

class TestWalletService:
    def test_topup_success(self, db_session, sample_wallet):
        service = WalletService(db_session)
        initial_balance = sample_wallet.balance
        
        result = service.topup(
            wallet_id=sample_wallet.id,
            amount=500.00,
            payment_method='eft'
        )
        
        assert result.balance == initial_balance + 500.00
        assert Transaction.query.count() == 1
    
    def test_topup_invalid_amount(self, db_session, sample_wallet):
        service = WalletService(db_session)
        
        with pytest.raises(ValueError):
            service.topup(
                wallet_id=sample_wallet.id,
                amount=-100.00,
                payment_method='eft'
            )
    
    def test_purchase_electricity_insufficient_balance(self, db_session, sample_wallet):
        service = WalletService(db_session)
        sample_wallet.balance = 50.00
        
        with pytest.raises(InsufficientBalanceError):
            service.purchase_electricity(
                wallet_id=sample_wallet.id,
                amount=100.00
            )
```

#### Day 3-4: Integration Tests
```python
# tests/integration/test_api_estates.py
import pytest
from base64 import b64encode

class TestEstateAPI:
    def test_list_estates(self, client, auth_headers):
        response = client.get('/api/v1/estates', headers=auth_headers)
        assert response.status_code == 200
        assert 'data' in response.json
        assert 'page' in response.json
    
    def test_create_estate_success(self, client, admin_headers):
        data = {
            "code": "TEST001",
            "name": "Test Estate",
            "total_units": 50
        }
        response = client.post('/api/v1/estates', 
                              json=data, 
                              headers=admin_headers)
        assert response.status_code == 201
        assert response.json['data']['code'] == "TEST001"
    
    def test_create_estate_duplicate_code(self, client, admin_headers, sample_estate):
        data = {
            "code": sample_estate.code,
            "name": "Another Estate",
            "total_units": 30
        }
        response = client.post('/api/v1/estates', 
                              json=data, 
                              headers=admin_headers)
        assert response.status_code == 409
```

#### Day 5: Performance Tests
```python
# tests/performance/test_load.py
import pytest
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        self.auth = b64encode(b"admin:password").decode('ascii')
        self.headers = {"Authorization": f"Basic {self.auth}"}
    
    @task(3)
    def list_estates(self):
        self.client.get("/api/v1/estates", headers=self.headers)
    
    @task(2)
    def get_estate_detail(self):
        self.client.get("/api/v1/estates/uuid-here", headers=self.headers)
    
    @task(1)
    def list_units(self):
        self.client.get("/api/v1/units?estate_id=uuid", headers=self.headers)
```

### AI Tasks for Sprint 3
1. **Test Generation**
   ```prompt
   Generate comprehensive pytest tests for the WalletService including:
   - Happy path scenarios
   - Edge cases (zero amounts, negative balances)
   - Concurrent update handling
   - Transaction rollback scenarios
   ```

2. **Fixture Generation**
   ```prompt
   Create pytest fixtures for:
   - Sample estates with units
   - Wallets with various balances
   - Rate tables with different structures
   - Mock meter readings
   ```

3. **Performance Optimization**
   ```prompt
   Analyze this query and suggest optimizations:
   [paste slow query]
   Include index recommendations and query refactoring
   ```

### Deliverables
- All API endpoints complete
- 80%+ test coverage achieved
- Integration tests passing
- Performance benchmarks met
- Load testing completed

---

## Sprint 4: Integration & Deployment (Week 8)

### Objectives
- System integration testing
- Deployment preparation
- Documentation finalization
- Performance tuning

### Day 1-2: System Integration
- [ ] End-to-end testing of all workflows
- [ ] API security testing
- [ ] Database backup/restore testing
- [ ] Error handling verification

### Day 3-4: Deployment Setup
```bash
# Docker configuration
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "src.wsgi:app"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/quantify
    depends_on:
      - db
  
  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=quantify
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Day 5: Documentation & Handover
- [ ] API documentation with examples
- [ ] Deployment guide
- [ ] Troubleshooting guide
- [ ] Performance tuning guide

### Deliverables
- Production-ready API
- Docker containers
- Deployment documentation
- Performance benchmarks

---

## Risk Management

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Database performance issues | High | Medium | Early performance testing, indexing strategy |
| Complex rate calculations | High | Medium | Thorough testing, calculation caching |
| Concurrent update conflicts | Medium | High | Optimistic locking, transaction isolation |
| Data migration errors | High | Low | Comprehensive validation, rollback plan |
| API security vulnerabilities | High | Medium | Security testing, code review |

### Mitigation Strategies
1. **Regular Testing**: Continuous testing throughout development
2. **Code Reviews**: AI-assisted and peer reviews
3. **Performance Monitoring**: Early identification of bottlenecks
4. **Security Scanning**: Automated vulnerability scanning
5. **Backup Strategy**: Regular backups during development

---

## Quality Assurance

### Code Quality Standards
- **Coverage Target**: 80% minimum
- **Linting**: Black, Flake8, mypy
- **Documentation**: Docstrings for all public methods
- **Reviews**: All PRs require review

### Testing Strategy
1. **Unit Tests**: All business logic
2. **Integration Tests**: API endpoints
3. **Performance Tests**: Load testing
4. **Security Tests**: OWASP top 10

### CI/CD Pipeline
```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        black --check src tests
        flake8 src tests
        mypy src
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=src --cov-report=html
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## Resource Requirements

### Development Team
- **Backend Developer**: 1 senior Python developer
- **Database Engineer**: Part-time for schema optimization
- **QA Engineer**: For test strategy and automation
- **DevOps**: Part-time for deployment setup

### Infrastructure
- **Development**: Local PostgreSQL, Redis
- **Staging**: Cloud VM (2 vCPU, 4GB RAM)
- **CI/CD**: GitHub Actions
- **Monitoring**: Sentry, New Relic (optional)

### Tools & Services
- **Version Control**: GitHub
- **Project Management**: Jira/GitHub Projects
- **Documentation**: Confluence/Markdown
- **API Testing**: Postman/Insomnia
- **Load Testing**: Locust

---

## Success Metrics

### Sprint Metrics
- **Velocity**: Story points completed per sprint
- **Code Coverage**: >80%
- **Bug Density**: <5 bugs per 1000 LOC
- **API Response Time**: <200ms average

### Project Success Criteria
1. **Functional**: All Phase 1 requirements implemented
2. **Performance**: Handles 100 concurrent users
3. **Quality**: Zero critical bugs in production
4. **Security**: Passes security audit
5. **Documentation**: Complete API documentation

---

## Communication Plan

### Daily Standups
- Time: 9:00 AM
- Duration: 15 minutes
- Focus: Progress, blockers, plans

### Sprint Reviews
- When: End of each sprint
- Duration: 1 hour
- Attendees: All stakeholders

### Retrospectives
- When: After sprint review
- Duration: 45 minutes
- Focus: Improvements

### Documentation
- Code comments: Inline
- API docs: Swagger/OpenAPI
- Wiki: Confluence/GitHub Wiki

---

## Appendix A: AI Development Prompts

### Model Generation
```
Generate a SQLAlchemy model for [entity] with:
- UUID primary key
- Audit columns (created_at, updated_at)
- Proper relationships
- Validation constraints
- Indexes for common queries
```

### API Endpoint Generation
```
Create a Flask blueprint for [resource] with:
- CRUD operations
- Pagination support
- Error handling
- Request validation
- Role-based access control
```

### Test Generation
```
Generate pytest tests for [feature] including:
- Happy path tests
- Edge cases
- Error scenarios
- Mock external dependencies
- Fixtures for test data
```

### Documentation Generation
```
Generate API documentation for [endpoint] including:
- Request/response examples
- Error codes
- Authentication requirements
- Rate limits
```

---

## Appendix B: Database Seed Script

```python
# scripts/seed_data.py
import random
from datetime import datetime, timedelta
from app.models import Estate, Unit, Resident, Wallet, Transaction
from app.core.database import SessionLocal

def seed_estates():
    """Create sample estates"""
    estates = [
        {"code": "WC001", "name": "Willow Creek", "total_units": 50},
        {"code": "OG001", "name": "Oak Gardens", "total_units": 75}
    ]
    # Implementation

def seed_units(estate_id, count):
    """Create units for an estate"""
    for i in range(count):
        unit = Unit(
            estate_id=estate_id,
            unit_number=f"{chr(65 + i // 25)}-{101 + i % 25}",
            floor=["Ground", "First", "Second"][i % 3],
            bedrooms=random.choice([1, 2, 3]),
            bathrooms=random.choice([1, 2])
        )
        # Create wallet and meters
        # Implementation

def seed_transactions(wallet_id, days=90):
    """Generate transaction history"""
    for day in range(days):
        date = datetime.now() - timedelta(days=day)
        # Generate random transactions
        # Implementation

if __name__ == "__main__":
    seed_estates()
    print("Seeding completed!")
```

---

## Appendix C: Make Commands

```makefile
# Makefile
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make dev        - Run development server"
	@echo "  make test       - Run tests"
	@echo "  make coverage   - Run tests with coverage"
	@echo "  make lint       - Run linters"
	@echo "  make migrate    - Run database migrations"
	@echo "  make seed       - Seed database"
	@echo "  make clean      - Clean cache files"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev:
	FLASK_ENV=development flask run --debug

test:
	pytest tests/ -v

coverage:
	pytest tests/ -v --cov=src --cov-report=html
	open htmlcov/index.html

lint:
	black src tests
	flake8 src tests
	mypy src

migrate:
	alembic upgrade head

seed:
	python scripts/seed_data.py

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov .coverage .pytest_cache
```

---

## Phase 2 Overview (Future Development)

### Mobile Application Development (4-6 weeks)
After successful completion of Phase 1, Phase 2 will focus on:

#### Mobile App Features
- **Native Apps**: iOS (Swift) and Android (Kotlin) or React Native
- **User Authentication**: Secure login for residents
- **Dashboard**: Real-time balance and consumption
- **Wallet Management**: Top-up and purchase utilities
- **Push Notifications**:
  - Low balance alerts (< R50)
  - Service disconnection warnings
  - Payment confirmations
  - Reconnection notifications
  - Maintenance announcements
- **Usage Analytics**: Consumption graphs and trends
- **Statement Downloads**: PDF statements

#### Backend Enhancements for Mobile
- **Push Notification Service**:
  - Firebase Cloud Messaging (FCM) for Android
  - Apple Push Notification Service (APNS) for iOS
  - Notification queue management
  - Delivery tracking and retry logic
- **Mobile API Endpoints**:
  - Device registration for push tokens
  - Mobile-optimized data responses
  - Offline capability support
- **Payment Gateway Integration**:
  - EFT payment processing
  - Credit/Debit card payments
  - Payment confirmation webhooks

#### Meter Integration
- **Physical Meter Connection**:
  - E460 Smart Prepayment Meters
  - DC450 Data Concentrator integration
  - Real-time data collection (15-minute intervals)
  - Automatic meter reading validation
- **Real-time Updates**:
  - WebSocket connections for live data
  - Automatic disconnection at zero balance
  - Instant reconnection on credit purchase

### Phase 3: Pilot Testing (2-3 weeks)
- User acceptance testing with residents
- Performance optimization
- Bug fixes and refinements
- Training and documentation
- Production deployment

---

## Document Version History

- v1.0 - Initial project plan for Phase 1 backend development
- v1.1 - Added Phase 2 overview with mobile app and push notifications

---

*End of Project Plan - Phase 1 Development*
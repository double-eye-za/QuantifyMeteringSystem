# Team Onboarding Guide - Quantify Metering System

Welcome to the Quantify Metering System project! This guide will help you get started.

## Repository Access

### GitHub Repository
- **URL**: https://github.com/willieprinsloo/QuantifyMeteringSystem
- **Clone via SSH**: `git@github.com:willieprinsloo/QuantifyMeteringSystem.git`
- **Clone via HTTPS**: `https://github.com/willieprinsloo/QuantifyMeteringSystem.git`

### Getting Started

1. **Clone the Repository**:
   ```bash
   git clone git@github.com:willieprinsloo/QuantifyMeteringSystem.git
   cd QuantifyMeteringSystem
   ```

2. **View the Prototype**:
   ```bash
   # Open the main dashboard in your browser
   open prototype/index.html
   # Or on Windows: start prototype/index.html
   ```

3. **Read Key Documentation**:
   - Start here: `README.md`
   - System overview: `documents/Functional Specification v3 - Based on Prototype.md`
   - Database design: `documents/Database Schema Documentation.md`
   - API reference: `documents/API Documentation.md`
   - Development plan: `documents/Project Plan - Phase 1 Development.md`

## Project Overview

### What is this?
A prepaid utility management system for residential estates with:
- Wallet-based prepaid billing
- Smart meter integration (electricity, water, solar)
- Configurable low balance alerts
- Multiple rate table options
- Real-time consumption monitoring

### Current Status
- ✅ **Phase 0**: Prototype completed (HTML/CSS/JS)
- ✅ **Phase 0**: Documentation completed
- 🚧 **Phase 1**: Backend development (6-8 weeks)
- 📅 **Phase 2**: Mobile app & meter integration
- 📅 **Phase 3**: Pilot testing

## Quick Links

### Live Demo Pages
Open these files in your browser:
- **Login**: `prototype/login.html` (Demo: admin/admin123)
- **Dashboard**: `prototype/index.html`
- **Estates**: `prototype/estates.html`
- **Units**: `prototype/units.html`
- **Billing**: `prototype/billing.html`
- **Rate Tables**: `prototype/rate-tables-simplified.html`
- **Settings**: `prototype/settings.html` (see Wallet & Meters tab)

### Key Features to Review
1. **Wallet System**: Prepaid with configurable alerts
2. **Meter Minimums**: R20 minimum for activation
3. **Rate Builder**: Multiple pricing models supported
4. **Smart Alerts**: Based on consumption patterns
5. **Payment Ready**: API designed for gateway integration

## Development Setup (Phase 1)

### Technology Stack
- **Backend**: Python 3.9+, Flask 3.0+
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy 2.0+
- **Testing**: pytest (80% coverage target)
- **Auth**: Basic Authentication

### Prerequisites
```bash
# Install Python 3.9+
python --version

# Install PostgreSQL
psql --version

# Install Git
git --version
```

### Environment Setup (When development starts)
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (when available)
pip install -r requirements.txt
```

## Team Communication

### Project Structure
```
QuantifyMeteringSystem/
├── prototype/          # HTML prototype (current)
├── documents/         # All documentation
├── src/              # Source code (Phase 1)
├── tests/            # Unit tests (Phase 1)
└── README.md         # Project overview
```

### Branches
- `main` - Production ready code
- `develop` - Development branch (create in Phase 1)
- `feature/*` - Feature branches

### Commit Messages
Use clear, descriptive messages:
```
feat: Add wallet top-up endpoint
fix: Correct meter activation logic
docs: Update API documentation
test: Add wallet service tests
```

## Key Contacts

### Project Roles
- **Project Owner**: [Your Name]
- **Technical Lead**: [TBD]
- **Backend Developer**: [TBD]
- **Frontend Developer**: [TBD]
- **QA/Testing**: [TBD]

## Important Notes

### Business Rules
1. **Electricity**: Disconnects at R0, requires R20 to reconnect
2. **Water**: Never disconnects, can go into debt
3. **Solar**: 50 kWh free monthly allocation
4. **Alerts**: Configurable per estate

### Security Considerations
- No JWT - using Basic Auth
- All passwords must be hashed
- Payment gateway integration ready
- POPIA compliance required

## Questions?

1. Review the documentation in `/documents`
2. Check the prototype in `/prototype`
3. Contact the project owner
4. Create an issue on GitHub

## Next Steps

### For Developers
1. Review `documents/development_guidelines.md`
2. Study the database schema
3. Familiarize yourself with the API specification
4. Review the unit test documentation

### For Stakeholders
1. Test the prototype thoroughly
2. Review the functional specification
3. Provide feedback via GitHub issues
4. Approve Phase 1 timeline

---

Welcome aboard! Let's build something great together. 🚀
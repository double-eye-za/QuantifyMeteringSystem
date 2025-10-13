# Quantify Metering System

A comprehensive prepaid utility management platform for residential estates, providing automated meter reading, wallet-based billing, and real-time consumption monitoring.

## Overview

The Quantify Metering System is designed to manage prepaid electricity, water, and solar metering for residential complexes. It provides an integrated solution for property management companies to monitor and bill individual units while offering residents a convenient mobile application for managing their utility accounts.

## Key Features

- **Smart Metering Infrastructure**: E460 smart prepayment meters for electricity and solar
- **Prepaid Wallet System**: Digital wallet for utility purchases with configurable alerts
- **Real-time Monitoring**: Live consumption tracking and instant credit application
- **Tiered Rate Tables**: Support for multiple pricing models (tiered, time-of-use, seasonal)
- **Meter Activation Controls**: Minimum balance requirements for service activation
- **Comprehensive Reporting**: Estate consumption, reconciliation, and financial reports
- **Multi-tenant Architecture**: Support for multiple estates with per-estate configurations

## Project Structure

```
quantify-metering/
├── documents/           # Technical documentation
│   ├── API Documentation.md
│   ├── Database Schema Documentation.md
│   ├── Functional Specification v3.md
│   ├── Project Plan - Phase 1 Development.md
│   └── Unit Test Documentation.md
├── prototype/          # HTML/CSS/JS prototype
│   ├── index.html     # Main dashboard
│   ├── estates.html   # Estate management
│   ├── units.html     # Unit management
│   ├── meters.html    # Meter monitoring
│   ├── billing.html   # Billing dashboard
│   └── ...           # Other prototype pages
└── documents/reference documents/  # Reference materials
```

## Technology Stack

### Backend (Phase 1)
- **Language**: Python 3.9+
- **Framework**: Flask 3.0+
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy 2.0+
- **Authentication**: Basic Auth with role-based access

### Frontend (Prototype)
- **HTML5/CSS3**: Responsive design
- **Tailwind CSS**: Utility-first styling
- **JavaScript**: Interactive components
- **Chart.js**: Data visualization

## Development Phases

### Phase 1: Backend & Admin Portal (Current)
- Database implementation
- RESTful API development
- Admin web portal
- Unit testing (80% coverage)
- Basic authentication

### Phase 2: Mobile App & Meter Integration
- Native mobile applications (iOS/Android)
- Physical meter integration (E460, DC450)
- Payment gateway integration
- Push notifications
- Real-time data collection

### Phase 3: Pilot Testing
- User acceptance testing
- Performance optimization
- Production deployment

## Installation & Setup

### Prerequisites
- Python 3.9+
- PostgreSQL 14+
- Git

### Quick Start

1. Clone the repository:
```bash
git clone git@github.com:willieprinsloo/QuantifyMeteringSystem.git
cd QuantifyMeteringSystem
```

2. Review documentation:
- Start with `documents/Functional Specification v3 - Based on Prototype.md`
- Review `documents/Database Schema Documentation.md` for database design
- Check `documents/API Documentation.md` for API endpoints

3. View the prototype:
```bash
# Open prototype/index.html in your browser
open prototype/index.html
```

## Key Business Rules

### Electricity
- Prepaid model with automatic disconnection at R0.00
- Minimum R20.00 required for reconnection
- Configurable markup (default 20%)

### Water
- Prepaid tracking but no physical disconnection
- Can accumulate debt (negative balance)
- Minimum R20.00 to begin tracking

### Solar
- 50 kWh free monthly allocation
- Excess usage billed at standard rates

### Wallet Alerts
- Configurable thresholds (fixed amount or days remaining)
- Smart alerts based on consumption patterns
- Frequency limiting to prevent spam

## Documentation

- **[Functional Specification](documents/Functional%20Specification%20v3%20-%20Based%20on%20Prototype.md)**: Complete system requirements and features
- **[Database Schema](documents/Database%20Schema%20Documentation.md)**: PostgreSQL database design
- **[API Documentation](documents/API%20Documentation.md)**: RESTful API endpoints and examples
- **[Project Plan](documents/Project%20Plan%20-%20Phase%201%20Development.md)**: Development timeline and milestones
- **[Unit Test Documentation](documents/Unit%20Test%20Documentation.md)**: Testing strategy and examples

## Contributing

Please review the development guidelines in `documents/development_guidelines.md` before contributing.

## License

Proprietary - Quantify Metering System

## Contact

For more information about the Quantify Metering System, please contact the development team.

---

**Version**: 1.0.0  
**Last Updated**: October 2025
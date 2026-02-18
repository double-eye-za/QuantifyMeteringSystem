# Quantify Metering System Documentation

This folder contains all technical documentation for the Quantify Metering System.

## Documentation Index

### Getting Started
| Document | Description |
|----------|-------------|
| [INSTALLATION.md](INSTALLATION.md) | Local development setup guide |
| [SERVER_SETUP.md](SERVER_SETUP.md) | Production server deployment |
| [TEAM_ONBOARDING.md](TEAM_ONBOARDING.md) | New developer onboarding guide |
| [COMPANY_ACCESS_GUIDE.md](COMPANY_ACCESS_GUIDE.md) | GitHub repository access setup |
| [DEVELOPMENT_GUIDELINES.md](DEVELOPMENT_GUIDELINES.md) | Technical guidelines for Python/Flask development |

### Project Overview
| Document | Description |
|----------|-------------|
| [BUSINESS_REQUIREMENTS.md](BUSINESS_REQUIREMENTS.md) | Business requirements specification |
| [STYLE_GUIDE.md](STYLE_GUIDE.md) | UI/UX design standards for admin portal |

### Architecture & Infrastructure
| Document | Description |
|----------|-------------|
| [SINGLE_DATABASE_SETUP.md](SINGLE_DATABASE_SETUP.md) | Shared database architecture for LoRaWAN integration |
| [NOTIFICATION_SYSTEM.md](NOTIFICATION_SYSTEM.md) | Celery/Redis notification system architecture |
| [HARD_CODED.md](HARD_CODED.md) | Technical debt audit - hardcoded values to address |
| [DATA_FLOW_INTEGRITY_AUDIT.md](audit/DATA_FLOW_INTEGRITY_AUDIT.md) | Comprehensive data integrity audit - CRUD, cascades, FK analysis |

### Features Documentation
| Document | Description |
|----------|-------------|
| [lorawan-chirpstack-integration.md](lorawan-chirpstack-integration.md) | LoRaWAN & ChirpStack integration guide |
| [METER_RELAY_CONTROL_PLAN.md](METER_RELAY_CONTROL_PLAN.md) | Remote meter disconnect/reconnect via LoRaWAN |
| [meter-off-service.md](meter-off-service.md) | Automated zero-balance meter disconnect service |
| [METER_CAPABILITIES.md](METER_CAPABILITIES.md) | Device capabilities matrix for different meter types |
| [DEVICE_COMMUNICATION_TYPES_IMPLEMENTATION.md](DEVICE_COMMUNICATION_TYPES_IMPLEMENTATION.md) | Dynamic device/communication types feature |
| [USER_DELETE_FEATURE.md](USER_DELETE_FEATURE.md) | User deletion functionality documentation |
| [MESSAGING_SYSTEM_PLAN.md](MESSAGING_SYSTEM_PLAN.md) | Broadcast messaging system for mobile users |
| [CONSUMPTION_BILLING_IMPLEMENTATION_PLAN.md](CONSUMPTION_BILLING_IMPLEMENTATION_PLAN.md) | Automatic wallet deductions based on consumption |
| [TABLE_FILTER_IMPROVEMENTS.md](TABLE_FILTER_IMPROVEMENTS.md) | AJAX-based table filtering UX improvements |

### Mobile App Integration
| Document | Description |
|----------|-------------|
| [MOBILE_API_ENDPOINTS.md](MOBILE_API_ENDPOINTS.md) | Mobile app API endpoints specification |
| [MOBILE_AUTH_IMPLEMENTATION_PLAN.md](MOBILE_AUTH_IMPLEMENTATION_PLAN.md) | Phone-based authentication implementation |
| [MOBILE_IMPLEMENTATION_SUMMARY.md](MOBILE_IMPLEMENTATION_SUMMARY.md) | Summary of completed mobile features |
| [API_DOCUMENTATION-mobile.md](API_DOCUMENTATION-mobile.md) | Comprehensive mobile API documentation |

### Refactoring & Migration Guides
| Document | Description |
|----------|-------------|
| [REFACTOR_PLAN_PERSON_MODEL.md](REFACTOR_PLAN_PERSON_MODEL.md) | Multi-person per unit architecture redesign |
| [DEPENDENCY_AUDIT_RESIDENT_TO_PERSON.md](DEPENDENCY_AUDIT_RESIDENT_TO_PERSON.md) | Resident to Person model migration audit |
| [MIGRATION_INSTRUCTIONS.md](MIGRATION_INSTRUCTIONS.md) | Database migration deployment guide |

### Work In Progress / Fix Plans
| Document | Description | Status |
|----------|-------------|--------|
| [FixMeterPage.md](FixMeterPage.md) | Meter details page improvements | Review needed |
| [METER_DETAILS_FIX_PLAN.md](METER_DETAILS_FIX_PLAN.md) | Replace hardcoded meter data | Review needed |

---

## Document Status Legend

- **Current**: Documentation is up-to-date with the codebase
- **Review needed**: May need updates to match current implementation
- **Planning**: Feature specification not yet implemented

## Contributing to Documentation

When adding new features:
1. Create a new `.md` file in this `docs/` folder
2. Add an entry to this README index
3. Use clear headings and code examples
4. Include API endpoints with request/response examples
5. Document any environment variables required

## Related Documentation

- Main project README: [../README.md](../README.md)
- Admin API documentation: [../documents/API Documentation V2.md](../documents/API%20Documentation%20V2.md)
- Hardware reference docs: [../documents/reference documents/](../documents/reference%20documents/)

# Business Requirements Specification (BRS)
## Quantify Metering System

---

**Document Information**
- **Document Title**: Business Requirements Specification - Quantify Metering System
- **Version**: 1.0
- **Date**: December 2024
- **Project**: Quantify Metering System
- **Phase**: Phase 1 (MVP)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Business Context](#2-business-context)
3. [Business Objectives](#3-business-objectives)
4. [Stakeholders](#4-stakeholders)
5. [Business Requirements](#5-business-requirements)
6. [Functional Requirements](#6-functional-requirements)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [Project Scope](#8-project-scope)
9. [Success Criteria](#9-success-criteria)
10. [Assumptions and Constraints](#10-assumptions-and-constraints)
11. [Risks and Dependencies](#11-risks-and-dependencies)

---

## 1. Executive Summary

The **Quantify Metering System** is a comprehensive platform designed to manage prepaid electricity, water, and solar metering for residential complexes. The system provides an integrated solution for property management companies to monitor and bill individual units while offering residents a convenient mobile application for managing their utility accounts.

### Key Features:
- **Smart Metering Infrastructure**: E460 smart prepayment meters for electricity and solar, with compatible smart water meters
- **Mobile Application**: Resident portal for balance management, payments, and usage monitoring
- **Admin Portal**: Web-based management system for property managers with complete functionality
- **Prepaid Wallet System**: Digital wallet exclusively for prepaid utility purchases
- **Real-time Monitoring**: Live consumption tracking and instant credit application
- **Complex Metering Setup**: 3 meters per unit (electricity, water, solar) + 2 bulk meters per complex for total consumption monitoring

---

## 2. Business Context

### 2.1 Market Opportunity
The system addresses the growing need for efficient utility management in residential complexes, providing:
- Automated meter reading and billing
- Improved revenue collection through prepaid models
- Enhanced tenant experience through digital platforms
- Reduced operational costs for property management

### 2.2 Target Market
- **Initial Deployment**: 2 residential estates with approximately 50 units each (100 units total)
- **Phase 1 Capacity**: Support for up to 150 meters per estate (450 total meters across both estates)
- **Primary**: Residential complexes and developments
- **Secondary**: Property management companies managing multiple estates
- **Future Expansion**: Individual property owners with multiple units

---

## 3. Business Objectives

### 3.1 Primary Objectives
1. **Create Complex Water/Electricity Metering**: Implement comprehensive metering system for residential complexes with individual unit monitoring
2. **Automate Utility Management**: Replace manual meter reading and billing processes with automated smart metering
3. **Improve Cash Flow**: Implement prepaid billing model to reduce arrears and improve collection rates
4. **Enable Wallet-Based Management**: Provide residents with digital wallets for loading credits and managing utility accounts
5. **Enhance Customer Experience**: Provide residents with convenient digital access to their utility accounts
6. **Reduce Operational Costs**: Minimize manual intervention in meter reading, billing, and payment collection

### 3.2 Secondary Objectives
1. **Data Analytics**: Provide insights into consumption patterns and revenue trends
2. **Scalability**: Design system to support expansion beyond initial 150 meters
3. **Integration**: Seamlessly integrate with existing property management systems
4. **Compliance**: Ensure POPIA compliance and data security standards

---

## 4. Stakeholders

### 4.1 Primary Stakeholders
- **SuperAdmin (Mike and Kerry)**: System administrators with full access and control
- **Residents/Tenants**: End users of the mobile application
- **Property Managers**: Users of the admin portal
- **Property Owners**: Beneficiaries of improved revenue collection

### 4.2 Secondary Stakeholders
- **Utility Companies**: Providers of electricity and water services
- **Payment Service Providers**: EFT and card payment processors
- **Meter Manufacturers**: E460 and water meter suppliers

### 4.3 Internal Stakeholders
- **Development Team**: System implementation and maintenance
- **Quantify Metering Team**: Feedback provision and key decision making
- **Management**: Strategic oversight and project governance

---

## 5. Business Requirements

### 5.1 Meter Infrastructure Requirements
- **Electricity Meters**: E460 Smart Prepayment Meters with power line carrier (PLC) communication
- **Water Meters**: Compatible smart meters with communication capabilities
  - Water meters bottleneck (restrict flow) when credit depleted, do not fully disconnect
- **Solar Meters**: E460 meters for monitoring solar consumption and billing
- **Bulk Meters**: Two input meters for monitoring total complex consumption (water and electricity)
- **Data Concentrators**: DC450 units for aggregating meter data and secure transmission
  - Primary DC450 located at complex main meter for bulk meter monitoring
  - Additional DC450 units deployed throughout complex for unit meter coverage

### 5.2 Meter Configuration Per Complex
- **Per Unit**: 3 meters (electricity, water, solar)
- **Per Complex**: 2 bulk input meters (water and electricity) for monitoring total complex consumption and billing
- **Communication**: Power line carrier via DC450 Data Concentrator
  - One DC450 Data Concentrator located at the complex main meter for bulk meter monitoring
  - Additional DC450 units as needed for unit-level meter communication
- **Data Flow**: Real-time consumption data transmission to backend system
- **Purpose**: Bulk meters monitor total complex consumption while individual unit meters track per-unit usage for billing purposes

### 5.3 Wallet and Payment Requirements
- **Prepaid Only**: Wallet system exclusively for prepaid utility purchases
- **Payment Methods**: 
  - Electronic Funds Transfer (EFT)
  - Credit/Debit Card payments
- **Instant Application**: Credit applied to meters immediately upon payment confirmation
- **Balance Management**: Real-time balance updates and low credit alerts

### 5.4 Notification Requirements
- **Low Credit Alerts**: Automated notifications when balances fall below threshold
- **Payment Confirmations**: Immediate confirmation of successful payments
- **Disconnection Notices**: Alerts when services are disconnected due to insufficient credit (electricity and solar)
- **Water Bottleneck Notices**: Alerts when water service is restricted due to insufficient credit (flow rate limited, not disconnected)
- **Reconnection Notices**: Confirmation when services are restored after payment
- **Delivery Methods**: SMS, Email, and Push notifications

### 5.5 Reporting Requirements
- **Low Credit Reports**: List of units with insufficient credit balances
- **Payment Reports**: Transaction history and revenue summaries  
- **Disconnection Reports**: Units with disconnected services
- **Consumption Reports**: Usage patterns and trends analysis
- **Revenue Reports**: Income tracking and arrears monitoring
- **Complex Consumption Reports**: Bulk meter data for total complex consumption monitoring

### 5.6 Complex Metering Architecture Requirements
**Unit-Level Metering:**
- Each residential unit requires 3 meters:
  - 1x E460 Electricity Meter (for electricity consumption)
  - 1x Compatible Smart Water Meter (for water consumption)
  - 1x E460 Solar Meter (for solar consumption billing)

**Complex-Level Metering:**
- Each complex requires 2 bulk input meters:
  - 1x Bulk Electricity Input Meter (monitors total complex electricity consumption)
  - 1x Bulk Water Input Meter (monitors total complex water consumption)
- Each complex requires DC450 Data Concentrator(s):
  - One DC450 Data Concentrator located at the complex main meter
  - Additional DC450 units deployed as needed for optimal coverage of unit meters

**Purpose and Function:**
- Individual unit meters: Track consumption for billing each resident
- Bulk meters: Monitor total complex consumption for overall management and verification
- Solar meters: Track solar consumption for billing purposes (not generation monitoring)

**Water Credit Depletion Behavior:**
- **Electricity**: Service disconnects when credit reaches R0
- **Water**: Service does not disconnect when credit reaches R0; instead, water flow is bottlenecked (restricted flow rate)
- **Solar**: Service disconnects when credit reaches R0
- Residents are notified when credits are low and when water service is bottlenecked

---

## 6. Functional Requirements

### 6.1 Mobile Application Requirements
- **User Authentication**: Secure login and account management
- **Balance Display**: Real-time credit balance for electricity, water, and solar
- **Usage Monitoring**: Current consumption rates and historical usage charts
- **Payment Processing**: Wallet top-up via EFT or card payment
- **Credit Purchase**: Buy utility credits for specific meters
- **Statement History**: View past transactions and usage records
- **Notification Center**: Manage and view all system notifications

### 6.2 Admin Portal Requirements
- **User Management**: Create, modify, and manage resident accounts
- **Meter Management**: Register, configure, and monitor all meters
- **Complex Setup**: Configure sites, units, and meter relationships
- **Tariff Management**: Set and update utility pricing (when tariffs are available)
- **Bulk Operations**: Upload meter data and user information via CSV/Excel
- **Dashboard**: Real-time overview of system status and key metrics
- **Reporting**: Generate and export various business reports

### 6.3 Backend System Requirements
- **Data Collection**: Receive and process meter readings from DC450 concentrators
- **Payment Processing**: Handle EFT and card payment transactions
- **Credit Management**: Apply purchased credits to appropriate meters
- **Notification Engine**: Send automated alerts via multiple channels
- **Security**: Implement POPIA compliance and OWASP ASVS L2 standards
- **Integration**: Connect with payment gateways and notification services

---

## 7. Non-Functional Requirements

### 7.1 Performance Requirements
- **Data Ingestion**: Meter readings available within 60 seconds
- **Validation**: Confirmed readings available within 5 minutes
- **Wallet Sync**: Instant credit application to meters
- **Response Time**: Mobile app response time under 3 seconds
- **Availability**: 99.5% system uptime SLA

### 7.2 Security Requirements
- **Data Protection**: POPIA compliant data handling and storage
- **Encryption**: TLS 1.2+ for data in transit, encryption at rest
- **Access Control**: Role-Based Access Control (RBAC) implementation
- **Audit Trails**: Complete logging of all transactions and system activities
- **Token Security**: Secure handling of payment tokens and wallet transactions

### 7.3 Scalability Requirements
- **Phase 1 Capacity**: Support for up to 150 meters
- **Architecture**: Scalable design for future expansion
- **Database**: Optimized for growing data volumes
- **API Design**: RESTful APIs supporting multiple clients

### 7.4 Usability Requirements
- **Mobile Interface**: Intuitive design for residents of all technical levels
- **Admin Interface**: Efficient workflows for property managers
- **Responsive Design**: Compatible with various screen sizes and devices
- **Accessibility**: Compliance with accessibility standards

---

## 8. Project Scope

### 8.1 Phase 1 – Administrative System and Meter Integration (4-6 weeks)
**Objective:** Establish the foundational admin system and meter communication infrastructure

**Included:**
- E460 smart meter integration for electricity and solar consumption billing
- Water meter integration (compatible smart meters)
- DC450 Data Concentrator setup and configuration
- Admin portal development (complete functionality)
  - User management
  - Meter management
  - Complex and unit setup
  - Tariff management
  - Bulk operations (CSV/Excel uploads)
  - Dashboard and monitoring
  - Reporting functionality (low credit, payments, disconnections)
- Backend system development
  - Data collection and processing from meters
  - Database architecture
  - API infrastructure
  - Security implementation (POPIA compliance)
- Meter installation and integration testing to ensure proper functionality

**Deliverables:**
- Fully functional admin portal
- Working meter communication infrastructure
- Backend APIs ready for mobile app integration
- Test meter installations in both estates

### 8.2 Phase 2 – Mobile App and Payment Gateway
**Objective:** Develop resident-facing mobile application and integrate payment processing

**Included:**
- Mobile application development (iOS and Android)
  - User authentication and account management
  - Balance display for electricity, water, and solar
  - Usage monitoring and historical charts
  - Wallet management interface
  - Statement history
  - Notification center
- Payment gateway integration
  - EFT payment processing
  - Credit/Debit card payment processing
  - Wallet top-up functionality
  - Credit purchase and application to meters
- Notification system implementation
  - SMS notifications
  - Email notifications
  - Push notifications
  - Notification types: low credit, payments, disconnections, reconnections
- Backend enhancements
  - Payment processing service
  - Wallet management system
  - Notification engine
  - Credit application to meters

**Deliverables:**
- Functional mobile application (iOS and Android)
- Working payment gateway integration
- Active notification system
- Complete end-to-end payment flow

### 8.3 Phase 3 – Pilot App Testing and Fixes
**Objective:** Deploy pilot version, conduct testing with real users, and resolve issues

**Included:**
- Pilot deployment to selected users in both estates
- User acceptance testing (UAT)
- Performance testing under real-world conditions
- Bug fixes and issue resolution
- User feedback collection and implementation
- System optimization and refinement
- User training and onboarding
- Documentation and support materials
- Final adjustments before full rollout

**Deliverables:**
- Stable, tested mobile application
- Resolved issues and bugs
- User documentation and training materials
- System ready for full production deployment
- Performance metrics and user satisfaction data

### 8.4 Future Enhancements (Post-Phase 3)
**Excluded from Initial Release:**
- Post-paid billing functionality
- Advanced analytics and forecasting
- Additional payment providers (PayFast, PayGate, Ozow, SnapScan)
- IoT integration for smart home management
- Advanced load control features
- AI-based anomaly detection
- Predictive consumption forecasting

---

## 9. Success Criteria

### 9.1 Phase 1 Success Criteria (Admin System and Meter Integration)
**Technical Criteria:**
- All meters successfully integrated and communicating with DC450 concentrators
- Admin portal operational with complete functionality
- Real-time data flow from meters to backend system
- Backend APIs functional and documented
- POPIA compliance implementation complete
- Meter data visible in admin dashboard

**Business Criteria:**
- Reduced manual meter reading by 100%
- Property managers can effectively manage meters and users
- Reports provide actionable business insights (low credit, payments, disconnections)
- Successful handling of 450 meters (150 per estate) without performance issues
- Zero security incidents during integration testing

### 9.2 Phase 2 Success Criteria (Mobile App and Payment Gateway)
**Technical Criteria:**
- Mobile application functional on iOS and Android
- Payment processing working for EFT and credit/debit card payments
- Wallet system operational with real-time balance updates
- Credit application to meters working instantly
- Notification system delivering alerts reliably

**Business Criteria:**
- Secure payment gateway integration with zero security breaches
- End-to-end payment flow functional (wallet top-up to meter credit)
- All notification types working (SMS, email, push)
- Mobile app passes internal quality assurance testing

### 9.3 Phase 3 Success Criteria (Pilot Testing and Fixes)
**Technical Criteria:**
- 99.5% system availability achieved during pilot
- All critical bugs identified and resolved
- Performance metrics meet specified requirements
- System stability under real-world usage

**Business Criteria:**
- Improved payment collection rates through prepaid system
- Positive user feedback from pilot participants
- User adoption rate meets targets
- System ready for full production rollout

**User Acceptance Criteria:**
- Residents can successfully top up wallets and purchase credits
- Property managers can effectively manage entire estates
- Notifications are delivered reliably and timely
- System is intuitive for users with varying technical expertise
- Support documentation enables self-service user assistance

---

## 10. Assumptions and Constraints

### 10.1 Assumptions
- E460 meters and DC450 concentrators will be available for testing
- Payment gateway providers will provide necessary API access
- Property management companies will provide required meter installation access
- Internet connectivity will be available at all meter locations
- Residents will have access to smartphones or internet-enabled devices

### 10.2 Constraints
- **Budget**: Allocated per phase with distinct deliverables
- **Timeline**: 
  - Phase 1: 4-6 weeks (Admin system and meter integration)
  - Phase 2: To be determined (Mobile app and payment gateway)
  - Phase 3: To be determined (Pilot testing and fixes)
- **Meter Capacity**: Initial limit of 150 meters per estate (450 total across both estates)
- **Compliance**: Must meet POPIA requirements
- **Payment Methods**: Limited to EFT and credit/debit card payments (Phase 2+)
- **Tariff Information**: Not yet available, to be provided during Phase 1
- **Wallet Functionality**: Prepaid only - no postpaid billing
- **Water Meter Type**: May differ from E460 meters (compatible smart meters required)
- **Phased Deployment**: Admin system must be complete before mobile app development begins

### 10.3 Dependencies

**Phase 1 Dependencies:**
- Meter installation and configuration by qualified technicians
- Network infrastructure at both estate locations
- Regulatory approvals for meter installations
- Access to existing property management systems (if integration required)
- Tariff information provision for billing configuration
- Water meter compatibility verification with E460 communication protocols
- DC450 Data Concentrator hardware availability

**Phase 2 Dependencies:**
- Phase 1 completion (admin system and meter integration fully functional)
- Payment gateway account setup and testing (EFT and credit/debit card providers)
- SMS and email notification service provider accounts
- Push notification service setup (iOS and Android)
- Mobile app store developer accounts (Apple and Google)

**Phase 3 Dependencies:**
- Phase 2 completion (mobile app and payment gateway functional)
- Selection of pilot users from both estates
- User training materials and support documentation
- Quantify Metering Team availability for feedback and decisions
- Issue tracking and resolution process in place

---

## 11. Risks and Dependencies

### 11.1 Technical Risks
- **Meter Communication Issues**: Risk of connectivity problems between meters and concentrators
- **Payment Gateway Integration**: Potential delays in payment processing setup
- **Data Synchronization**: Risk of data inconsistencies between meters and applications
- **Scalability Concerns**: System performance under load testing

**Mitigation Strategies:**
- Comprehensive testing of meter communication protocols
- Early engagement with payment gateway providers
- Robust error handling and data validation
- Performance testing with maximum expected load

### 11.2 Business Risks
- **User Adoption**: Residents may resist digital payment methods
- **Regulatory Changes**: Potential changes in POPIA or utility regulations
- **Competition**: Other solutions entering the market
- **Technical Support**: Need for ongoing system maintenance and support

**Mitigation Strategies:**
- User training and support programs
- Regular compliance reviews and updates
- Continuous market analysis and competitive positioning
- Dedicated support team and documentation

### 11.3 Project Risks
- **Timeline Delays**: Risk of missing phase deadlines (especially Phase 1: 4-6 weeks)
- **Resource Availability**: Potential shortage of development or testing resources across phases
- **Scope Creep**: Uncontrolled expansion of requirements within each phase
- **Quality Issues**: Risk of delivering substandard functionality
- **Phase Dependencies**: Delays in early phases cascade to subsequent phases
- **Pilot Testing Delays**: Extended Phase 3 due to unforeseen issues or user feedback

**Mitigation Strategies:**
- Regular project monitoring and milestone tracking for each phase
- Resource planning and backup resource identification
- Strict change control processes with phase-specific requirements
- Comprehensive testing and quality assurance procedures at end of each phase
- Buffer time built into Phase 2 and Phase 3 timelines
- Clear phase completion criteria before moving to next phase
- Quantify Metering Team regular engagement for timely decision making

---

## Appendices

### Appendix A: Glossary
- **E460**: Smart prepayment electricity meter model
- **DC450**: Data concentrator for aggregating meter communications
- **PLC**: Power Line Carrier communication protocol
- **STS**: Standard Transfer Specification for secure token vending
- **POPIA**: Protection of Personal Information Act (South African privacy law)
- **OWASP ASVS**: Open Web Application Security Project Application Security Verification Standard

### Appendix B: References
- Original Functional Specification: Quantify Metering
- POPIA Compliance Guidelines
- OWASP ASVS Level 2 Requirements
- E460 Meter Technical Specifications
- DC450 Data Concentrator Documentation

---

**Document Approval**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Business Analyst | [To be filled] | | |
| Project Manager | [To be filled] | | |
| Technical Lead | [To be filled] | | |
| Business Owner | [To be filled] | | |

---

*This document serves as the foundation for the Quantify Metering System development and should be reviewed and updated as requirements evolve throughout the project lifecycle.*

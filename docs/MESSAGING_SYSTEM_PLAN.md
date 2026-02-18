# Messaging System Implementation Plan

## Overview
A broadcast messaging system that allows admin users to send messages to mobile app users. Messages can be sent to all users, users in a specific estate, or individual users.

---

## Database Design

### Messages Table (`messages`)
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER | NO | Primary key, auto-increment |
| subject | VARCHAR(255) | NO | Message subject/title |
| content | TEXT | NO | Message body content |
| message_type | VARCHAR(20) | NO | 'broadcast', 'estate', 'individual' |
| sender_user_id | INTEGER | NO | FK to users table (admin who sent) |
| estate_id | INTEGER | YES | FK to estates table (for estate messages) |
| recipient_person_id | INTEGER | YES | FK to persons table (for individual messages) |
| recipient_count | INTEGER | NO | Number of recipients (cached) |
| created_at | DATETIME | NO | When message was created |
| sent_at | DATETIME | YES | When message was sent |

### Message Recipients Table (`message_recipients`)
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER | NO | Primary key, auto-increment |
| message_id | INTEGER | NO | FK to messages table |
| person_id | INTEGER | NO | FK to persons table |
| is_read | BOOLEAN | NO | Default FALSE |
| read_at | DATETIME | YES | When message was read |
| created_at | DATETIME | NO | When recipient record created |

**Indexes:**
- `message_recipients`: (message_id, person_id) - unique
- `message_recipients`: (person_id, is_read) - for unread queries

---

## Tasks Checklist

### Phase 1: Backend - Database & Models
- [x] Create Message model (`app/models/message.py`)
- [x] Create MessageRecipient model (`app/models/message_recipient.py`)
- [x] Update models `__init__.py` to export new models
- [x] Create database migration
- [x] Run migration

### Phase 2: Backend - Service Layer
- [x] Create message service (`app/services/messages.py`)
  - [x] `create_message()` - Create and send message
  - [x] `get_message_by_id()` - Get single message with stats
  - [x] `list_messages()` - List all messages with filters
  - [x] `delete_message()` - Delete a message
  - [x] `get_message_stats()` - Dashboard statistics
  - [x] `_send_to_all_users()` - Helper to create recipients for broadcast
  - [x] `_send_to_estate()` - Helper to create recipients for estate
  - [x] `_send_to_individual()` - Helper to create recipient for individual

### Phase 3: Backend - Website Routes
- [x] Create message routes (`app/routes/v1/messages.py`)
  - [x] `GET /messages` - Messages list page
  - [x] `GET /messages/compose` - Compose message page
  - [x] `POST /messages` - Create/send message API
  - [x] `GET /messages/<id>` - Message detail page
  - [x] `DELETE /api/messages/<id>` - Delete message API
  - [x] `GET /api/messages/stats` - Get statistics API
  - [x] `GET /api/messages/recipients` - Search recipients API
- [x] Register routes in `app/routes/v1/__init__.py`

### Phase 4: Backend - Website Templates
- [x] Create messages list template (`app/templates/messages/messages.html`)
  - [x] Stats cards (Total sent, Broadcast, Estate, Individual)
  - [x] Messages table with filters
  - [x] Pagination
- [x] Create compose message template (`app/templates/messages/compose.html`)
  - [x] Recipient type selector (All/Estate/Individual)
  - [x] Dynamic estate dropdown
  - [x] Person search/select for individual
  - [x] Subject and content fields
  - [x] Preview before send
- [x] Create message detail template (`app/templates/messages/message-detail.html`)
  - [x] Message content display
  - [x] Delivery statistics
  - [x] Read receipts list
- [x] Add navigation link to sidebar (`app/templates/base.html`)

### Phase 5: Backend - Mobile API
- [x] Create mobile message routes (`app/routes/mobile/messages.py`)
  - [x] `GET /messages` - List messages for current user
  - [x] `GET /messages/<id>` - Get message detail (marks as read)
  - [x] `PUT /messages/<id>/read` - Mark message as read
  - [x] `GET /messages/unread-count` - Get unread count
- [x] Register routes in `app/routes/mobile/__init__.py`

### Phase 6: Mobile App - Models & Repository
- [x] Create Message model (`lib/models/message_model.dart`)
- [x] Create Message repository (`lib/repositories/message_repository.dart`)

### Phase 7: Mobile App - Screens
- [x] Create Messages screen (`lib/screens/messages/messages_screen.dart`)
  - [x] List of messages with filter tabs (All/Unread/Read)
  - [x] Unread indicator with badge
  - [x] Pull to refresh
- [x] Create Message detail screen (`lib/screens/messages/message_detail_screen.dart`)
  - [x] Full message content with type badge
  - [x] Auto-mark as read when viewing
- [x] Add navigation to app drawer with unread badge
- [x] Add polling for new messages (30 second interval)

---

## API Endpoints Summary

### Website API (Staff)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/messages` | List all messages |
| POST | `/api/v1/messages` | Create/send message |
| GET | `/api/v1/messages/<id>` | Get message details |
| DELETE | `/api/v1/messages/<id>` | Delete message |
| GET | `/api/v1/messages/stats` | Get statistics |
| GET | `/api/v1/messages/search-persons` | Search persons for recipient |

### Mobile API (Residents)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/mobile/messages` | List user's messages |
| GET | `/api/mobile/messages/<id>` | Get message (marks read) |
| PUT | `/api/mobile/messages/<id>/read` | Mark as read |
| GET | `/api/mobile/messages/unread-count` | Get unread count |

---

## UI Mockups

### Website - Messages List
```
+----------------------------------------------------------+
| Messages                                    [+ New Message]|
+----------------------------------------------------------+
| [Total: 45] [Broadcast: 12] [Estate: 20] [Individual: 13] |
+----------------------------------------------------------+
| Search...                    [Type ▼] [Estate ▼] [Date ▼] |
+----------------------------------------------------------+
| Subject          | Type      | Recipients | Sent     | Read|
|------------------|-----------|------------|----------|-----|
| System Update    | Broadcast | 1,234      | 2 hrs ago| 45% |
| Water Outage     | Estate    | 89         | 1 day ago| 78% |
| Account Notice   | Individual| 1          | 3 days   | Yes |
+----------------------------------------------------------+
```

### Website - Compose Message
```
+----------------------------------------------------------+
| Compose Message                                           |
+----------------------------------------------------------+
| Send To:  ( ) All Users  ( ) Estate  ( ) Individual      |
|                                                           |
| [Estate Dropdown - shown if Estate selected]              |
| [Person Search - shown if Individual selected]            |
|                                                           |
| Subject: [____________________________________]           |
|                                                           |
| Message:                                                  |
| [                                                    ]    |
| [                                                    ]    |
| [                                                    ]    |
|                                                           |
| Recipients: 1,234 users will receive this message         |
|                                                           |
|                              [Cancel] [Preview] [Send]    |
+----------------------------------------------------------+
```

### Mobile - Messages Inbox
```
+---------------------------+
| Messages              (3) |
+---------------------------+
| * System Update           |
|   Important changes...    |
|   2 hours ago             |
+---------------------------+
| * Water Maintenance       |
|   Scheduled outage...     |
|   1 day ago               |
+---------------------------+
|   Welcome to Quantify     |
|   Thank you for...        |
|   1 week ago              |
+---------------------------+
```

---

## Progress Tracking

**Started:** December 2024
**Completed:** December 2024
**Status:** COMPLETE

### Completed
- [x] Initial planning
- [x] Created this plan document
- [x] Phase 1: Database & Models
- [x] Phase 2: Backend Service Layer
- [x] Phase 3: Website Routes
- [x] Phase 4: Website Templates
- [x] Phase 5: Mobile API
- [x] Phase 6: Mobile App Models & Repository
- [x] Phase 7: Mobile App Screens

---

## Notes
- Messages are one-way (admin to users) - no replies
- Consider adding push notifications in future
- Consider adding scheduled messages in future
- Consider adding message templates in future

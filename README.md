# Django + Celery Budget Management System

A comprehensive budget management system for advertising campaigns with automated budget enforcement, dayparting, and REST API endpoints.

## Features

- **Budget Tracking**: Daily and monthly budget limits per brand and campaign
- **Automated Enforcement**: Celery tasks automatically pause campaigns when budgets are exceeded
- **Dayparting**: Campaigns only run during specified time windows
- **REST API**: Full CRUD operations for brands, campaigns, and spend tracking
- **Admin Interface**: Django admin for manual management
- **Type Safety**: Full type hints with mypy configuration
- **Comprehensive Testing**: 20+ tests covering all functionality

## Tech Stack

- **Backend**: Django 5.2+
- **Task Queue**: Celery with Redis
- **Database**: SQLite (configurable for production)
- **Type Checking**: mypy
- **Testing**: Django TestCase

## Quick Start

### Prerequisites

- Python 3.10+
- Redis server
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ramgirirakesh7/Django-remote-job.git
   cd Django-remote-job
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**
   ```bash
   python manage.py migrate
   ```

4. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

5. **Start Redis**
   ```bash
   redis-server
   ```

6. **Start Django server**
   ```bash
   python manage.py runserver
   ```

7. **Start Celery worker (in new terminal)**
   ```bash
   celery -A budget_manager worker -l info
   ```

8. **Start Celery beat (in new terminal)**
   ```bash
   celery -A budget_manager beat -l info
   ```

## API Endpoints

### Brands

#### Get All Brands
```http
GET /api/brands/
```

**Response:**
```json
{
  "brands": [
    {
      "id": 1,
      "name": "Brand X",
      "daily_budget": "1000.00",
      "monthly_budget": "30000.00",
      "campaigns_count": 2
    }
  ]
}
```

#### Create Brand
```http
POST /api/brands/create/
Content-Type: application/json

{
  "name": "New Brand",
  "daily_budget": "500.00",
  "monthly_budget": "15000.00"
}
```

**Response:**
```json
{
  "id": 2,
  "name": "New Brand",
  "daily_budget": "500.00",
  "monthly_budget": "15000.00"
}
```

### Campaigns

#### Get All Campaigns
```http
GET /api/campaigns/
```

**Response:**
```json
{
  "campaigns": [
    {
      "id": 1,
      "name": "Summer Sale",
      "brand": "Brand X",
      "brand_id": 1,
      "is_active": true,
      "daily_spend": "150.00",
      "monthly_spend": "1500.00",
      "dayparting_start": "09:00",
      "dayparting_end": "17:00",
      "daily_budget": "1000.00",
      "monthly_budget": "30000.00"
    }
  ]
}
```

#### Create Campaign
```http
POST /api/campaigns/create/
Content-Type: application/json

{
  "name": "Winter Campaign",
  "brand_id": 1,
  "dayparting_start": "10:00",
  "dayparting_end": "18:00"
}
```

**Response:**
```json
{
  "id": 2,
  "name": "Winter Campaign",
  "brand": "Brand X",
  "is_active": true,
  "dayparting_start": "10:00",
  "dayparting_end": "18:00"
}
```

### Spend Management

#### Add Spend to Campaign
```http
POST /api/spend/add/
Content-Type: application/json

{
  "campaign_id": 1,
  "amount": "50.00"
}
```

**Response:**
```json
{
  "campaign_id": 1,
  "campaign_name": "Summer Sale",
  "amount": "50.00",
  "new_daily_spend": "200.00",
  "new_monthly_spend": "1550.00",
  "is_active": true
}
```

**Error Response (if budget exceeded):**
```json
{
  "error": "Spend would exceed budget limits"
}
```

#### Get Spend Logs
```http
GET /api/spend/logs/
```

**With filters:**
```http
GET /api/spend/logs/?campaign_id=1&date=2024-01-15
```

**Response:**
```json
{
  "spend_logs": [
    {
      "id": 1,
      "campaign_name": "Summer Sale",
      "brand_name": "Brand X",
      "date": "2024-01-15",
      "amount": "50.00"
    }
  ]
}
```

### System Status

#### Get System Overview
```http
GET /api/status/
```

**Response:**
```json
{
  "total_brands": 2,
  "total_campaigns": 5,
  "active_campaigns": 3,
  "paused_campaigns": 2,
  "over_daily_budget": 1,
  "over_monthly_budget": 0,
  "server_time": "2024-01-15T10:30:00Z"
}
```

## Management Commands

### Simulate Spend
Simulate random spend events for all active campaigns:

```bash
python manage.py simulate_spend
```

**Output:**
```
Added spend 45 to Summer Sale
Added spend 78 to Winter Campaign
```

## Celery Tasks

The system runs several automated tasks:

- **Budget Checking** (every 5 minutes): Pauses campaigns that exceed budgets
- **Dayparting Enforcement** (every 5 minutes): Activates/deactivates campaigns based on time windows
- **Daily Reset** (midnight): Resets daily spends and reactivates eligible campaigns
- **Monthly Reset** (1st of month): Resets monthly spends

## Admin Interface

Access the Django admin at `http://127.0.0.1:8000/admin/` to:

- Manage brands and their budgets
- Create and configure campaigns
- View spend logs
- Monitor system status

## Testing

Run the complete test suite:

```bash
python manage.py test
```

**Test Coverage:**
- Model creation and relationships
- API endpoints (CRUD operations)
- Celery task functionality
- Management commands
- Integration workflows

## Type Checking

Run mypy to check type safety:

```bash
mypy .
```

## Project Structure

```
├── budget_manager/          # Django project settings
│   ├── settings.py         # Main configuration
│   ├── urls.py            # URL routing
│   ├── celery.py          # Celery configuration
│   └── wsgi.py            # WSGI application
├── core/                   # Main application
│   ├── models.py          # Database models
│   ├── views.py           # API endpoints
│   ├── tasks.py           # Celery tasks
│   ├── admin.py           # Admin interface
│   ├── tests.py           # Test suite
│   └── management/        # Management commands
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── mypy.ini              # Type checking configuration
└── README.md             # This file
```

## Environment Variables

For production, set these environment variables:

```bash
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com
CELERY_BROKER_URL=redis://your-redis-server:6379/0
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions, please open an issue on GitHub. 
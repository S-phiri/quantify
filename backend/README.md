# Django Backend for Finance App

This is the Django backend that provides API endpoints for the finance application.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py migrate
```

3. Start the development server:
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## API Endpoints

### File Upload
- `POST /api/upload/` - Upload CSV files
- `GET /api/upload/{id}/status/` - Get upload status and preview
- `POST /api/upload/{id}/process/` - Process uploaded file
- `GET /api/upload/history/` - Get upload history

### Dashboard Data
- `GET /api/dashboard/` - Get dashboard KPIs
- `GET /api/transactions/` - Get recent transactions
- `GET /api/holdings/` - Get current holdings
- `GET /api/insights/` - Get financial insights

### Authentication
- `GET /api/auth/csrf/` - Get CSRF token

## File Types Supported

1. **Transactions** - Bank statements, credit card transactions
   - Required columns: Date, Amount, Description
   
2. **Holdings** - Investment portfolios, stock holdings
   - Required columns: Symbol, Quantity, Price
   
3. **Trades** - Buy/sell orders, trading activity
   - Required columns: Date, Symbol, Action, Quantity, Price

## Development Notes

- The current implementation uses mock data storage
- For production, replace with proper database models
- Add proper authentication and user management
- Implement real financial calculations and analysis
- Add data validation and error handling

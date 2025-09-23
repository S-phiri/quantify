# Finance App - Current State Document

## 🏗️ **Project Architecture**
- **Frontend**: Next.js 15 + Tailwind CSS + shadcn/ui + Recharts
- **Backend**: Django 5.2.6 + SQLite + django-cors-headers
- **Charts**: Recharts (pie, bar, line charts)
- **Currency**: South African Rands (R)

## 📁 **Project Structure**
```
Finance app/
├── backend/
│   ├── ingestor/           # Main Django app
│   │   ├── models.py       # Transaction, Holding, Trade models
│   │   ├── views.py        # API endpoints (524 lines)
│   │   ├── urls.py         # URL routing
│   │   └── admin.py        # Django admin
│   ├── settings.py         # Django configuration
│   └── urls.py             # Project URLs
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   └── dashboard/
│   │   │       └── page.tsx # Main dashboard component
│   │   ├── lib/
│   │   │   └── api.ts      # API functions (65 lines)
│   │   └── components/
│   │       └── charts/     # Chart components
│   └── package.json
└── manage.py
```

## ✅ **Working Features**
1. **CSV Upload & Processing**
   - File upload with drag & drop
   - CSV parsing for transactions
   - Automatic data type detection
   - Database storage

2. **Dashboard Analytics**
   - Dynamic KPIs (Total Spending, Income, Net Worth)
   - Real-time data updates
   - Three chart types implemented

3. **API Endpoints**
   - `/api/upload/` - File upload
   - `/api/dashboard/` - Dashboard data
   - `/api/transactions/` - Transaction list
   - `/api/holdings/` - Holdings data
   - `/api/insights/` - Financial insights
   - `/api/spending-categories/` - Category breakdown
   - `/api/monthly-data/` - Monthly trends
   - `/api/cash-flow-data/` - Cash flow analysis

4. **Chart Components**
   - `SpendingPieChart` - Category breakdown
   - `MonthlySpendingChart` - Monthly trends
   - `CashFlowChart` - Cash flow over time

## 🐛 **Current Issues (Priority Order)**

### 1. **Upload Process Messy** 🔴 HIGH PRIORITY
- File handling inconsistent
- Upload statistics not tracking properly
- History shows 0 for all uploads

### 2. **Currency Display Bug** 🔴 HIGH PRIORITY
- Shows "£R" instead of just "R"
- Affects all financial displays

### 3. **Pie Chart Issues** 🟡 MEDIUM PRIORITY
- Labels overlapping
- Duplicate "amount" legends (4 times)
- Poor readability

### 4. **Missing User Authentication** 🟡 MEDIUM PRIORITY
- No user system
- All data is global/shared
- No personalized experience

### 5. **Upload History Broken** 🔴 HIGH PRIORITY
- Upload statistics always show 0
- No proper tracking of uploads
- History functionality missing

## 🗄️ **Database Models**
```python
class Transaction(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    date = models.DateField()
    description = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=100, blank=True)
    account_type = models.CharField(max_length=50, default='checking')

class Holding(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=12, decimal_places=6)
    current_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_value = models.DecimalField(max_digits=12, decimal_places=2)

class Trade(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    symbol = models.CharField(max_length=20)
    trade_type = models.CharField(max_length=10, choices=[('BUY', 'Buy'), ('SELL', 'Sell')])
    quantity = models.DecimalField(max_digits=12, decimal_places=6)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField()
```

## 🔧 **Key Files to Modify**

### **Backend Files:**
- `backend/ingestor/views.py` - Fix upload tracking, currency display
- `backend/ingestor/models.py` - Add upload tracking model
- `backend/ingestor/urls.py` - Add auth endpoints

### **Frontend Files:**
- `frontend/src/lib/api.ts` - Fix currency formatting
- `frontend/src/components/charts/SpendingPieChart.tsx` - Fix overlapping labels
- `frontend/src/app/dashboard/page.tsx` - Update currency display

## 🚀 **Next Development Phase**
1. **Fix Upload System** (2-3 hours)
2. **Implement User Authentication** (4-6 hours)
3. **Add Portfolio Analysis** (1-2 days)
4. **Build AI Assistant** (2-4 hours)

## 📊 **Current Data Flow**
1. User uploads CSV → `upload_process` view
2. CSV parsed → Transaction/Holding objects created
3. Dashboard fetches data → API endpoints
4. Charts render → Recharts components
5. Real-time updates → React state management

## 🔐 **Authentication Status**
- **Current**: No authentication
- **Planned**: Django User model + JWT tokens
- **Impact**: All data currently global/shared

## 💰 **Currency Implementation**
- **Backend**: Decimal fields for precision
- **Frontend**: Formatting functions
- **Issue**: "£R" display bug
- **Fix**: Remove pound symbol, keep only "R"

---

**Last Updated**: January 2025
**Status**: Active Development
**Priority**: Fix upload system and currency display

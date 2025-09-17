from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.middleware.csrf import get_token
from .models import Transaction, Holding, Trade
import traceback
import uuid
import csv
from decimal import Decimal
from datetime import datetime

@require_GET
def health(request):
    return JsonResponse({"ok": True, "where": "django"})

@require_GET
@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({"csrfToken": get_token(request)})

@require_GET
def history(request):
    try:
        return JsonResponse([], safe=False)
    except Exception as e:
        return JsonResponse({"error": f"History error: {str(e)}"}, status=500)

@require_POST
@csrf_protect
def upload(request):
    try:
        if "file" not in request.FILES:
            return JsonResponse({"error": "No 'file' provided"}, status=400)
        f = request.FILES["file"]
        upload_id = str(uuid.uuid4())
        path = default_storage.save(f"uploads/{upload_id}_{f.name}", ContentFile(f.read()))
        return JsonResponse({
            "uploadId": upload_id,
            "message": "File uploaded successfully",
            "path": path,
            "name": f.name,
            "size": f.size
        })
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@require_GET
def upload_status(request, upload_id):
    try:
        # For now, return a mock status since we don't have a database
        return JsonResponse({
            "uploadId": upload_id,
            "status": "completed",
            "message": "File processed successfully"
        })
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
@csrf_protect
def upload_process(request, upload_id):
    try:
        # Find the uploaded file
        import os
        upload_dir = "uploads"
        if not os.path.exists(upload_dir):
            return JsonResponse({"error": "Upload directory not found"}, status=500)
        
        # Find the file with this upload_id
        files = [f for f in os.listdir(upload_dir) if f.startswith(upload_id)]
        if not files:
            return JsonResponse({"error": "File not found"}, status=404)
        
        file_path = os.path.join(upload_dir, files[0])
        
        # Parse the CSV file
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            print(f"[DEBUG] Processing CSV file: {file_path}")
            print(f"[DEBUG] CSV headers: {reader.fieldnames}")
            
            transactions_created = 0
            holdings_created = 0
            
            for row_num, row in enumerate(reader, 1):
                try:
                    print(f"[DEBUG] Processing row {row_num}: {row}")
                    
                    # Try to create a Transaction
                    if 'Date' in row and 'Description' in row and 'Amount' in row:
                        print(f"[DEBUG] Found transaction data in row {row_num}")
                        
                        # Parse date
                        date_str = row['Date']
                        if '/' in date_str:
                            # Handle DD/MM/YYYY format
                            day, month, year = date_str.split('/')
                            parsed_date = datetime(int(year), int(month), int(day)).date()
                        else:
                            # Handle YYYY-MM-DD format
                            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        
                        # Parse amount
                        amount_str = row['Amount'].replace('£', '').replace(',', '').strip()
                        amount = Decimal(amount_str)
                        
                        print(f"[DEBUG] Creating transaction: {parsed_date}, {row['Description']}, {amount}")
                        
                        # Create transaction
                        Transaction.objects.create(
                            date=parsed_date,
                            description=row['Description'],
                            amount=amount,
                            category=row.get('Category', ''),
                            account_type=row.get('Account', 'checking')
                        )
                        transactions_created += 1
                        print(f"[DEBUG] Transaction created successfully! Total: {transactions_created}")
                    
                    # Try to create a Holding
                    elif 'symbol' in row and 'quantity' in row and 'price' in row:
                        symbol = row['symbol']
                        quantity = Decimal(row['quantity'])
                        price = Decimal(row['price'])
                        total_value = quantity * price
                        
                        Holding.objects.create(
                            symbol=symbol,
                            name=row.get('name', symbol),
                            quantity=quantity,
                            current_price=price,
                            total_value=total_value
                        )
                        holdings_created += 1
                        
                except Exception as row_error:
                    print(f"[DEBUG] Error processing row {row_num}: {row_error}")
                    print(f"[DEBUG] Row data: {row}")
                    continue
        
        return JsonResponse({
            "uploadId": upload_id,
            "status": "completed",
            "message": f"File processed successfully. Created {transactions_created} transactions and {holdings_created} holdings.",
            "transactionsCreated": transactions_created,
            "holdingsCreated": holdings_created
        })
        
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

# Dashboard API endpoints
@require_GET
def dashboard(request):
    """Get dashboard overview data"""
    try:
        # Get basic stats
        total_transactions = Transaction.objects.count()
        total_holdings = Holding.objects.count()
        total_trades = Trade.objects.count()
        
        # Calculate financial metrics
        total_spending = sum(float(t.amount) for t in Transaction.objects.filter(amount__lt=0))
        total_income = sum(float(t.amount) for t in Transaction.objects.filter(amount__gt=0))
        net_worth = total_income + total_spending  # income is positive, spending is negative
        
        # Calculate portfolio value
        total_portfolio_value = sum(float(h.total_value) for h in Holding.objects.all())
        
        # Determine what data we have and show relevant KPIs
        has_transactions = total_transactions > 0
        has_holdings = total_holdings > 0
        
        kpis = []
        
        if has_transactions:
            # Show transaction-based KPIs
            kpis.extend([
                {
                    "title": "Total Spending",
                    "value": f"R{abs(total_spending):,.2f}",
                    "change": f"{abs(total_spending):,.0f}",
                    "changeType": "negative",
                    "icon": "CreditCard"
                },
                {
                    "title": "Total Income", 
                    "value": f"R{total_income:,.2f}",
                    "change": f"{total_income:,.0f}",
                    "changeType": "positive",
                    "icon": "TrendingUp"
                },
                {
                    "title": "Net Worth",
                    "value": f"R{net_worth:,.2f}",
                    "change": f"{net_worth:,.0f}",
                    "changeType": "positive" if net_worth >= 0 else "negative",
                    "icon": "PiggyBank"
                }
            ])
        
        if has_holdings:
            # Show portfolio-based KPIs
            kpis.extend([
                {
                    "title": "Portfolio Value",
                    "value": f"R{total_portfolio_value:,.2f}",
                    "change": f"{total_portfolio_value:,.0f}",
                    "changeType": "positive",
                    "icon": "Briefcase"
                },
                {
                    "title": "Active Holdings",
                    "value": f"{total_holdings:,}",
                    "change": f"{total_holdings}",
                    "changeType": "positive",
                    "icon": "PieChart"
                }
            ])
        
        # If no data, show empty state
        if not kpis:
            kpis = [
                {
                    "title": "No Data",
                    "value": "Upload CSV",
                    "change": "to get started",
                    "changeType": "neutral",
                    "icon": "Upload"
                }
            ]
        
        return JsonResponse({
            "kpis": kpis,
            "recentActivity": f"Dashboard loaded - {total_transactions} transactions, {total_holdings} holdings",
            "hasTransactions": has_transactions,
            "hasHoldings": has_holdings
        })
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@require_GET
def transactions(request):
    """Get recent transactions"""
    try:
        limit = int(request.GET.get('limit', 10))
        transactions = Transaction.objects.all().order_by('-date')[:limit]
        
        data = []
        for t in transactions:
            # Determine transaction type based on amount
            transaction_type = 'income' if float(t.amount) > 0 else 'expense'
            
            data.append({
                "id": t.id,
                "date": t.date.isoformat(),
                "description": t.description,
                "amount": float(t.amount),
                "category": t.category or 'Uncategorized',
                "accountType": t.account_type,
                "type": transaction_type
            })
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@require_GET
def holdings(request):
    """Get current holdings"""
    try:
        holdings = Holding.objects.all()
        
        data = []
        for h in holdings:
            data.append({
                "id": h.id,
                "symbol": h.symbol,
                "name": h.name,
                "quantity": float(h.quantity),
                "currentPrice": float(h.current_price),
                "totalValue": float(h.total_value)
            })
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@require_GET
def insights(request):
    """Get financial insights"""
    try:
        # Get transaction data
        transactions = Transaction.objects.all()
        total_transactions = transactions.count()
        
        if total_transactions == 0:
            return JsonResponse([], safe=False)
        
        # Calculate spending metrics
        spending_transactions = transactions.filter(amount__lt=0)
        income_transactions = transactions.filter(amount__gt=0)
        
        total_spending = sum(float(t.amount) for t in spending_transactions)
        total_income = sum(float(t.amount) for t in income_transactions)
        net_worth = total_income + total_spending
        
        # Calculate spending by category
        from collections import defaultdict
        category_spending = defaultdict(float)
        for t in spending_transactions:
            category = t.category or 'Uncategorized'
            category_spending[category] += abs(float(t.amount))
        
        # Get top spending categories
        top_categories = sorted(category_spending.items(), key=lambda x: x[1], reverse=True)[:3]
        
        insights_data = []
        
        # Net worth insight
        if net_worth >= 0:
            insights_data.append({
                "type": "positive",
                "title": "Positive Net Worth",
                "description": f"Great! Your net worth is R{net_worth:,.2f}",
                "icon": "TrendingUp"
            })
        else:
            insights_data.append({
                "type": "warning",
                "title": "Negative Net Worth",
                "description": f"Your net worth is R{net_worth:,.2f}. Consider reducing spending.",
                "icon": "TrendingDown"
            })
        
        # Spending analysis
        if total_spending != 0:
            insights_data.append({
                "type": "info",
                "title": "Spending Analysis",
                "description": f"You've spent R{abs(total_spending):,.2f} across {spending_transactions.count()} transactions",
                "icon": "CreditCard"
            })
        
        # Top spending categories
        if top_categories:
            top_category = top_categories[0]
            insights_data.append({
                "type": "info",
                "title": "Top Spending Category",
                "description": f"'{top_category[0]}' accounts for R{top_category[1]:,.2f} of your spending",
                "icon": "PieChart"
            })
        
        # Income analysis
        if total_income > 0:
            insights_data.append({
                "type": "positive",
                "title": "Income Summary",
                "description": f"Total income: R{total_income:,.2f} from {income_transactions.count()} transactions",
                "icon": "ArrowUp"
            })
        
        # Savings rate and emergency fund advice
        if total_income > 0:
            savings_rate = ((total_income + total_spending) / total_income) * 100
            monthly_net_income = total_income + total_spending  # This is net income per month
            
            if savings_rate > 20:
                insights_data.append({
                    "type": "positive",
                    "title": "Excellent Savings Rate",
                    "description": f"You're saving {savings_rate:.1f}% of your income!",
                    "icon": "PiggyBank"
                })
            elif savings_rate > 0:
                insights_data.append({
                    "type": "info",
                    "title": "Savings Rate",
                    "description": f"You're saving {savings_rate:.1f}% of your income",
                    "icon": "PiggyBank"
                })
            else:
                insights_data.append({
                    "type": "warning",
                    "title": "Negative Savings",
                    "description": f"You're spending {abs(savings_rate):.1f}% more than you earn",
                    "icon": "AlertTriangle"
                })
            
            # Emergency fund advice based on net income
            if monthly_net_income > 0:
                emergency_fund_target = monthly_net_income * 6  # 6 months of expenses
                insights_data.append({
                    "type": "info",
                    "title": "Emergency Fund Target",
                    "description": f"Based on your net income, aim for R{emergency_fund_target:,.2f} emergency fund (6 months)",
                    "icon": "Shield"
                })
            else:
                insights_data.append({
                    "type": "warning",
                    "title": "Emergency Fund Priority",
                    "description": "Focus on reducing expenses first, then build emergency fund",
                    "icon": "AlertTriangle"
                })
        
        return JsonResponse(insights_data, safe=False)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@require_GET
def spending_categories(request):
    """Get spending breakdown by category for pie chart"""
    try:
        # Get spending by category
        from collections import defaultdict
        category_spending = defaultdict(float)
        
        spending_transactions = Transaction.objects.filter(amount__lt=0)
        for t in spending_transactions:
            category = t.category or 'Uncategorized'
            category_spending[category] += abs(float(t.amount))
        
        # Convert to list format for frontend
        categories_data = []
        for category, amount in category_spending.items():
            categories_data.append({
                "category": category,
                "amount": float(amount),
                "percentage": 0  # Will be calculated on frontend
            })
        
        # Sort by amount descending
        categories_data.sort(key=lambda x: x['amount'], reverse=True)
        
        return JsonResponse(categories_data, safe=False)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@require_GET
def monthly_data(request):
    """Get monthly spending and income data for bar chart"""
    try:
        from django.db.models import Sum
        from datetime import datetime
        
        # Get transactions grouped by month
        transactions = Transaction.objects.all()
        
        monthly_data = {}
        for t in transactions:
            month_key = t.date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {'spending': 0, 'income': 0}
            
            if t.amount < 0:
                monthly_data[month_key]['spending'] += abs(float(t.amount))
            else:
                monthly_data[month_key]['income'] += float(t.amount)
        
        # Convert to list format
        chart_data = []
        for month, data in sorted(monthly_data.items()):
            chart_data.append({
                'month': datetime.strptime(month, '%Y-%m').strftime('%b %Y'),
                'spending': data['spending'],
                'income': data['income'],
                'net': data['income'] - data['spending']
            })
        
        return JsonResponse(chart_data, safe=False)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@require_GET
def cash_flow_data(request):
    """Get daily cash flow data for line chart"""
    try:
        from datetime import datetime, timedelta
        
        # Get transactions ordered by date
        transactions = Transaction.objects.all().order_by('date')
        
        if not transactions.exists():
            return JsonResponse([], safe=False)
        
        # Calculate daily and cumulative cash flow
        cash_flow_data = []
        cumulative_balance = 0
        
        # Group by date
        daily_totals = {}
        for t in transactions:
            date_str = t.date.strftime('%Y-%m-%d')
            if date_str not in daily_totals:
                daily_totals[date_str] = 0
            daily_totals[date_str] += float(t.amount)
        
        # Create cumulative data
        for date_str, daily_amount in sorted(daily_totals.items()):
            cumulative_balance += daily_amount
            cash_flow_data.append({
                'date': datetime.strptime(date_str, '%Y-%m-%d').strftime('%m/%d'),
                'daily': daily_amount,
                'cumulative': cumulative_balance
            })
        
        return JsonResponse(cash_flow_data, safe=False)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)
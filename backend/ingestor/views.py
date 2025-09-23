from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect, csrf_exempt
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.middleware.csrf import get_token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Transaction, Holding, Trade, Upload
import traceback
import uuid
import csv
from decimal import Decimal
from datetime import datetime
import json

@require_GET
def health(request):
    return JsonResponse({"ok": True, "where": "django"})

@ensure_csrf_cookie
@require_GET
def csrf_token(request):
    """Get CSRF token for API requests"""
    return JsonResponse({"csrfToken": get_token(request)})

@require_GET
@ensure_csrf_cookie
def csrf(request):
    token = get_token(request)
    response = JsonResponse({"csrfToken": token})
    # Explicitly set the CSRF cookie
    response.set_cookie('csrftoken', token, max_age=3600, httponly=False, samesite='Lax')
    return response

@require_GET
def history(request):
    try:
        # Filter uploads by user if authenticated, otherwise show all
        if request.user.is_authenticated:
            uploads = Upload.objects.filter(user=request.user).order_by('-created_at')
        else:
            uploads = Upload.objects.all().order_by('-created_at')
        upload_data = []
        
        for upload in uploads:
            upload_data.append({
                "id": str(upload.id),
                "filename": upload.filename,
                "fileType": upload.file_type,
                "status": upload.status,
                "transactionsCreated": upload.transactions_created,
                "holdingsCreated": upload.holdings_created,
                "tradesCreated": upload.trades_created,
                "createdAt": upload.created_at.isoformat(),
                "processedAt": upload.processed_at.isoformat() if upload.processed_at else None,
                "errorMessage": upload.error_message
            })
        
        # Calculate statistics
        total_files = uploads.count()
        successful = uploads.filter(status='completed').count()
        processing = uploads.filter(status='processing').count()
        failed = uploads.filter(status='failed').count()
        
        return JsonResponse({
            "uploads": upload_data,
            "statistics": {
                "totalFiles": total_files,
                "successful": successful,
                "processing": processing,
                "failed": failed
            }
        }, safe=False)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": f"History error: {str(e)}"}, status=500)

@require_POST
def upload(request):
    try:
        if "file" not in request.FILES:
            return JsonResponse({"error": "No 'file' provided"}, status=400)
        
        f = request.FILES["file"]
        file_type = request.POST.get("file_type", "transactions")
        upload_id = str(uuid.uuid4())
        
        # Create Upload record - associate with user if authenticated
        upload_record = Upload.objects.create(
            id=upload_id,
            user=request.user if request.user.is_authenticated else None,
            filename=f.name,
            file_type=file_type,
            status='uploaded'
        )
        
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
        upload_record = Upload.objects.get(id=upload_id)
        return JsonResponse({
            "uploadId": upload_id,
            "status": upload_record.status,
            "message": f"File {upload_record.status}",
            "transactionsCreated": upload_record.transactions_created,
            "holdingsCreated": upload_record.holdings_created,
            "tradesCreated": upload_record.trades_created,
            "errorMessage": upload_record.error_message
        })
    except Upload.DoesNotExist:
        return JsonResponse({"error": "Upload not found"}, status=404)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
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
        
        # Get the upload record to associate data with the user
        try:
            upload_record = Upload.objects.get(id=upload_id)
        except Upload.DoesNotExist:
            return JsonResponse({"error": "Upload record not found"}, status=404)
        
        # Parse the CSV file
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            print(f"[DEBUG] Processing CSV file: {file_path}")
            print(f"[DEBUG] CSV headers: {reader.fieldnames}")
            
            transactions_created = 0
            holdings_created = 0
            trades_created = 0
            
            # Check if this is a holdings file - if so, clear existing holdings first
            # (Holdings represent current state, so we replace them)
            first_row = next(reader, None)
            if first_row and 'symbol' in first_row and 'quantity' in first_row and 'price' in first_row:
                print(f"[DEBUG] Detected holdings data - clearing existing holdings for user")
                Holding.objects.filter(user=upload_record.user).delete()
            
            # Reset reader to beginning
            csvfile.seek(0)
            reader = csv.DictReader(csvfile)
            
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
                            user=upload_record.user,
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
                            user=upload_record.user,
                            symbol=symbol,
                            name=row.get('name', symbol),
                            quantity=quantity,
                            current_price=price,
                            total_value=total_value
                        )
                        holdings_created += 1
                    
                    # Try to create a Trade
                    elif 'Symbol' in row and 'Action' in row and 'Quantity' in row and 'Price' in row:
                        print(f"[DEBUG] Found trade data in row {row_num}")
                        
                        # Parse date
                        date_str = row['Date']
                        if '/' in date_str:
                            # Handle DD/MM/YYYY format
                            day, month, year = date_str.split('/')
                            parsed_date = datetime(int(year), int(month), int(day))
                        else:
                            # Handle YYYY-MM-DD format
                            parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                        
                        # Parse trade data
                        symbol = row['Symbol']
                        action = row['Action'].upper()  # BUY or SELL
                        quantity = Decimal(row['Quantity'])
                        price = Decimal(row['Price'])
                        total_amount = quantity * price
                        
                        print(f"[DEBUG] Creating trade: {parsed_date}, {symbol}, {action}, {quantity}, {price}")
                        
                        # Create trade
                        Trade.objects.create(
                            user=upload_record.user,
                            symbol=symbol,
                            trade_type=action,
                            quantity=quantity,
                            price=price,
                            total_amount=total_amount,
                            date=parsed_date
                        )
                        trades_created += 1
                        print(f"[DEBUG] Trade created successfully! Total: {trades_created}")
                        
                except Exception as row_error:
                    print(f"[DEBUG] Error processing row {row_num}: {row_error}")
                    print(f"[DEBUG] Row data: {row}")
                    continue
        
        # Update Upload record
        upload_record = Upload.objects.get(id=upload_id)
        upload_record.status = 'completed'
        upload_record.transactions_created = transactions_created
        upload_record.holdings_created = holdings_created
        upload_record.trades_created = trades_created
        upload_record.processed_at = datetime.now()
        upload_record.save()
        
        return JsonResponse({
            "uploadId": upload_id,
            "status": "completed",
            "message": f"File processed successfully. Created {transactions_created} transactions, {holdings_created} holdings, and {trades_created} trades.",
            "transactionsCreated": transactions_created,
            "holdingsCreated": holdings_created,
            "tradesCreated": trades_created
        })
        
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
def reset_all_data(request):
    """Reset all data - clear all transactions, holdings, trades, and uploads for the authenticated user"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        # Clear all data for the authenticated user only
        Transaction.objects.filter(user=request.user).delete()
        Holding.objects.filter(user=request.user).delete()
        Trade.objects.filter(user=request.user).delete()
        Upload.objects.filter(user=request.user).delete()
        
        return JsonResponse({
            "message": "All your data has been reset successfully",
            "status": "success"
        })
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

# Dashboard API endpoints
@require_GET
def dashboard(request):
    """Get dashboard overview data"""
    try:
        # Filter by user if authenticated, otherwise show all data
        if request.user.is_authenticated:
            transactions = Transaction.objects.filter(user=request.user)
            holdings = Holding.objects.filter(user=request.user)
        else:
            transactions = Transaction.objects.all()
            holdings = Holding.objects.all()
        
        # Get basic stats
        total_transactions = transactions.count()
        total_holdings = holdings.count()
        total_trades = Trade.objects.count()
        
        # Calculate financial metrics
        total_spending = sum(float(t.amount) for t in transactions.filter(amount__lt=0))
        total_income = sum(float(t.amount) for t in transactions.filter(amount__gt=0))
        net_worth = total_income + total_spending  # income is positive, spending is negative
        
        # Calculate portfolio value
        total_portfolio_value = sum(float(h.total_value) for h in holdings)
        
        # Determine what data we have and show relevant KPIs
        has_transactions = total_transactions > 0
        has_holdings = total_holdings > 0
        
        kpis = []
        
        if has_transactions:
            # Show transaction-based KPIs
            kpis.extend([
                {
                    "title": "Total Spending",
                    "value": f"{abs(total_spending):,.2f}",
                    "change": f"{abs(total_spending):,.0f}",
                    "changeType": "negative",
                    "icon": "CreditCard"
                },
                {
                    "title": "Total Income", 
                    "value": f"{total_income:,.2f}",
                    "change": f"{total_income:,.0f}",
                    "changeType": "positive",
                    "icon": "TrendingUp"
                },
                {
                    "title": "Net Worth",
                    "value": f"{net_worth:,.2f}",
                    "change": f"{net_worth:,.0f}",
                    "changeType": "positive" if net_worth >= 0 else "negative",
                    "icon": "PiggyBank"
                }
            ])
        
        if has_holdings:
            # Calculate portfolio metrics
            total_cost = sum(float(h.quantity * h.current_price) for h in holdings)  # Simplified cost calculation
            unrealized_pnl = total_portfolio_value - total_cost
            
            # Show portfolio-based KPIs
            kpis.extend([
                {
                    "title": "Portfolio Value",
                    "value": f"{total_portfolio_value:,.2f}",
                    "change": f"{total_portfolio_value:,.0f}",
                    "changeType": "positive",
                    "icon": "TrendingUp"
                },
                {
                    "title": "Total Cost",
                    "value": f"{total_cost:,.2f}",
                    "change": f"{total_cost:,.0f}",
                    "changeType": "neutral",
                    "icon": "DollarSign"
                },
                {
                    "title": "Unrealized P/L",
                    "value": f"{unrealized_pnl:,.2f}",
                    "change": f"{((unrealized_pnl/total_cost)*100):.1f}%" if total_cost > 0 else "0.0%",
                    "changeType": "positive" if unrealized_pnl >= 0 else "negative",
                    "icon": "PiggyBank"
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
        if request.user.is_authenticated:
            transactions = Transaction.objects.filter(user=request.user).order_by('-date')[:limit]
        else:
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
        if request.user.is_authenticated:
            holdings = Holding.objects.filter(user=request.user)
        else:
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

# Portfolio Analysis endpoints
@require_GET
def portfolio_analysis(request):
    """Get detailed portfolio analysis"""
    try:
        # Use authenticated user's data, fallback to demo user if not authenticated
        if request.user.is_authenticated:
            holdings = Holding.objects.filter(user=request.user)
        else:
            demo_user = User.objects.get(username='demo')
            holdings = Holding.objects.filter(user=demo_user)
        
        if not holdings.exists():
            return JsonResponse({
                "message": "No holdings data available",
                "analysis": {}
            })
        
        # Calculate portfolio metrics
        total_value = sum(float(h.total_value) for h in holdings)
        total_cost = sum(float(h.quantity * h.current_price) for h in holdings)
        unrealized_pnl = total_value - total_cost
        pnl_percentage = (unrealized_pnl / total_cost * 100) if total_cost > 0 else 0
        
        # Top performers
        holdings_data = []
        for h in holdings:
            holdings_data.append({
                "symbol": h.symbol,
                "name": h.name,
                "quantity": float(h.quantity),
                "current_price": float(h.current_price),
                "total_value": float(h.total_value),
                "weight": (float(h.total_value) / total_value * 100) if total_value > 0 else 0
            })
        
        # Sort by total value
        holdings_data.sort(key=lambda x: x['total_value'], reverse=True)
        
        return JsonResponse({
            "total_value": total_value,
            "total_cost": total_cost,
            "unrealized_pnl": unrealized_pnl,
            "pnl_percentage": pnl_percentage,
            "holdings_count": holdings.count(),
            "top_holdings": holdings_data[:5],  # Top 5 holdings
            "analysis": {
                "portfolio_health": "Good" if pnl_percentage > 0 else "Needs attention",
                "diversification_score": min(len(holdings_data) * 10, 100),  # Simple diversification score
                "risk_level": "Low" if len(holdings_data) > 5 else "Medium" if len(holdings_data) > 2 else "High"
            }
        })
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@require_GET
def trades_analysis(request):
    """Get trading analysis and performance metrics"""
    try:
        # Use authenticated user's data, fallback to demo user if not authenticated
        if request.user.is_authenticated:
            trades = Trade.objects.filter(user=request.user)
        else:
            demo_user = User.objects.get(username='demo')
            trades = Trade.objects.filter(user=demo_user)
        
        if not trades.exists():
            return JsonResponse({
                "message": "No trading data available",
                "analysis": {}
            })
        
        # Calculate trading metrics
        total_trades = trades.count()
        buy_trades = trades.filter(trade_type='BUY').count()
        sell_trades = trades.filter(trade_type='SELL').count()
        
        total_buy_amount = sum(float(t.total_amount) for t in trades.filter(trade_type='BUY'))
        total_sell_amount = sum(float(t.total_amount) for t in trades.filter(trade_type='SELL'))
        
        # Trading activity by symbol
        symbol_activity = {}
        for trade in trades:
            symbol = trade.symbol
            if symbol not in symbol_activity:
                symbol_activity[symbol] = {"buy": 0, "sell": 0, "volume": 0}
            
            symbol_activity[symbol][trade.trade_type.lower()] += 1
            symbol_activity[symbol]["volume"] += float(trade.total_amount)
        
        # Sort symbols by volume
        top_symbols = sorted(symbol_activity.items(), key=lambda x: x[1]["volume"], reverse=True)[:5]
        
        return JsonResponse({
            "total_trades": total_trades,
            "buy_trades": buy_trades,
            "sell_trades": sell_trades,
            "total_buy_amount": total_buy_amount,
            "total_sell_amount": total_sell_amount,
            "net_trading_activity": total_sell_amount - total_buy_amount,
            "top_traded_symbols": [
                {
                    "symbol": symbol,
                    "buy_count": data["buy"],
                    "sell_count": data["sell"],
                    "total_volume": data["volume"]
                }
                for symbol, data in top_symbols
            ],
            "analysis": {
                "trading_frequency": "High" if total_trades > 20 else "Medium" if total_trades > 5 else "Low",
                "buy_sell_ratio": buy_trades / sell_trades if sell_trades > 0 else float('inf'),
                "most_active_symbol": top_symbols[0][0] if top_symbols else None
            }
        })
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

# Authentication views
@require_POST
def user_login(request):
    """User login endpoint"""
    try:
        
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({"error": "Username and password are required"}, status=400)
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
            })
        else:
            return JsonResponse({"error": "Invalid username or password"}, status=401)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
def user_logout(request):
    """User logout endpoint"""
    try:
        logout(request)
        return JsonResponse({"message": "Logout successful"})
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
def user_signup(request):
    """User signup endpoint"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        if not username or not email or not password:
            return JsonResponse({"error": "Username, email, and password are required"}, status=400)
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Username already exists"}, status=400)
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({"error": "Email already exists"}, status=400)
        
        # Create new user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Log the user in
        login(request, user)
        
        return JsonResponse({
            "message": "Account created successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        })
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@require_GET
def user_profile(request):
    """Get current user profile"""
    try:
        if request.user.is_authenticated:
            return JsonResponse({
                "user": {
                    "id": request.user.id,
                    "username": request.user.username,
                    "email": request.user.email,
                    "first_name": request.user.first_name,
                    "last_name": request.user.last_name,
                    "is_authenticated": True
                }
            })
        else:
            return JsonResponse({"is_authenticated": False})
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)
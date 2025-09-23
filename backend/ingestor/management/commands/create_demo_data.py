from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from backend.ingestor.models import Transaction, Holding, Trade, Upload
from decimal import Decimal
from datetime import datetime, date, timedelta
import uuid

class Command(BaseCommand):
    help = 'Create demo data for the demo user'

    def handle(self, *args, **options):
        # Get demo user
        try:
            user = User.objects.get(username='demo')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Demo user does not exist! Run create_demo_user first.')
            )
            return

        # Clear existing demo data
        Transaction.objects.filter(user=user).delete()
        Holding.objects.filter(user=user).delete()
        Upload.objects.filter(user=user).delete()

        # Create sample transactions
        sample_transactions = [
            {'date': date(2024, 1, 15), 'description': 'Salary Deposit', 'amount': Decimal('5000.00'), 'category': 'Income', 'account_type': 'checking'},
            {'date': date(2024, 1, 16), 'description': 'Grocery Store', 'amount': Decimal('-150.00'), 'category': 'Food', 'account_type': 'checking'},
            {'date': date(2024, 1, 17), 'description': 'Gas Station', 'amount': Decimal('-45.00'), 'category': 'Transportation', 'account_type': 'checking'},
            {'date': date(2024, 1, 18), 'description': 'Coffee Shop', 'amount': Decimal('-8.50'), 'category': 'Food', 'account_type': 'checking'},
            {'date': date(2024, 1, 19), 'description': 'Netflix Subscription', 'amount': Decimal('-15.99'), 'category': 'Entertainment', 'account_type': 'checking'},
            {'date': date(2024, 1, 20), 'description': 'Electric Bill', 'amount': Decimal('-120.00'), 'category': 'Utilities', 'account_type': 'checking'},
            {'date': date(2024, 1, 21), 'description': 'Restaurant', 'amount': Decimal('-75.00'), 'category': 'Food', 'account_type': 'checking'},
            {'date': date(2024, 1, 22), 'description': 'ATM Withdrawal', 'amount': Decimal('-100.00'), 'category': 'Cash', 'account_type': 'checking'},
            {'date': date(2024, 1, 23), 'description': 'Online Shopping', 'amount': Decimal('-89.99'), 'category': 'Shopping', 'account_type': 'checking'},
            {'date': date(2024, 1, 24), 'description': 'Freelance Payment', 'amount': Decimal('800.00'), 'category': 'Income', 'account_type': 'checking'},
        ]

        for transaction_data in sample_transactions:
            Transaction.objects.create(
                user=user,
                **transaction_data
            )

        # Create sample holdings
        sample_holdings = [
            {'symbol': 'AAPL', 'name': 'Apple Inc.', 'quantity': Decimal('10.000000'), 'current_price': Decimal('150.00'), 'total_value': Decimal('1500.00')},
            {'symbol': 'TSLA', 'name': 'Tesla Inc.', 'quantity': Decimal('5.000000'), 'current_price': Decimal('200.00'), 'total_value': Decimal('1000.00')},
            {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'quantity': Decimal('8.000000'), 'current_price': Decimal('300.00'), 'total_value': Decimal('2400.00')},
            {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'quantity': Decimal('3.000000'), 'current_price': Decimal('2500.00'), 'total_value': Decimal('7500.00')},
            {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'quantity': Decimal('2.000000'), 'current_price': Decimal('3200.00'), 'total_value': Decimal('6400.00')},
        ]

        for holding_data in sample_holdings:
            Holding.objects.create(
                user=user,
                **holding_data
            )

        # Create sample trades
        sample_trades = [
            {'symbol': 'AAPL', 'trade_type': 'BUY', 'quantity': Decimal('10.000000'), 'price': Decimal('145.00'), 'total_amount': Decimal('1450.00'), 'date': datetime(2024, 1, 10)},
            {'symbol': 'TSLA', 'trade_type': 'BUY', 'quantity': Decimal('5.000000'), 'price': Decimal('195.00'), 'total_amount': Decimal('975.00'), 'date': datetime(2024, 1, 12)},
            {'symbol': 'MSFT', 'trade_type': 'BUY', 'quantity': Decimal('8.000000'), 'price': Decimal('295.00'), 'total_amount': Decimal('2360.00'), 'date': datetime(2024, 1, 15)},
            {'symbol': 'GOOGL', 'trade_type': 'BUY', 'quantity': Decimal('3.000000'), 'price': Decimal('2450.00'), 'total_amount': Decimal('7350.00'), 'date': datetime(2024, 1, 18)},
            {'symbol': 'AMZN', 'trade_type': 'BUY', 'quantity': Decimal('2.000000'), 'price': Decimal('3150.00'), 'total_amount': Decimal('6300.00'), 'date': datetime(2024, 1, 20)},
            {'symbol': 'AAPL', 'trade_type': 'SELL', 'quantity': Decimal('2.000000'), 'price': Decimal('155.00'), 'total_amount': Decimal('310.00'), 'date': datetime(2024, 1, 22)},
            {'symbol': 'TSLA', 'trade_type': 'SELL', 'quantity': Decimal('1.000000'), 'price': Decimal('210.00'), 'total_amount': Decimal('210.00'), 'date': datetime(2024, 1, 25)},
        ]

        for trade_data in sample_trades:
            Trade.objects.create(
                user=user,
                **trade_data
            )

        # Create sample upload record
        upload = Upload.objects.create(
            id=str(uuid.uuid4()),
            user=user,
            filename='demo_transactions.csv',
            file_type='transactions',
            status='completed',
            transactions_created=len(sample_transactions),
            holdings_created=len(sample_holdings),
            processed_at=datetime.now()
        )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created demo data for user: {user.username}')
        )
        self.stdout.write(f'Created {len(sample_transactions)} transactions')
        self.stdout.write(f'Created {len(sample_holdings)} holdings')
        self.stdout.write(f'Created {len(sample_trades)} trades')
        self.stdout.write(f'Created 1 upload record')

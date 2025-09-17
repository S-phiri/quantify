from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Transaction(models.Model):
    """Financial transaction model for bank statements, credit cards, etc."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    description = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=100, blank=True)
    account_type = models.CharField(max_length=50, default='checking')  # checking, savings, credit, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.date} - {self.description} - ${self.amount}"

class Holding(models.Model):
    """Investment holding model for portfolios, stocks, etc."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    symbol = models.CharField(max_length=20)  # AAPL, TSLA, etc.
    name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=12, decimal_places=6)
    current_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_value = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-total_value']
    
    def __str__(self):
        return f"{self.symbol} - {self.quantity} shares @ ${self.current_price}"

class Trade(models.Model):
    """Trading activity model for buy/sell orders"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    symbol = models.CharField(max_length=20)
    trade_type = models.CharField(max_length=10, choices=[('BUY', 'Buy'), ('SELL', 'Sell')])
    quantity = models.DecimalField(max_digits=12, decimal_places=6)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.trade_type} {self.quantity} {self.symbol} @ ${self.price}"

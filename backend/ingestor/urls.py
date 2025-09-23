from django.urls import path
from .views import (
    upload, history, upload_status, upload_process, reset_all_data,
    dashboard, transactions, holdings, insights, spending_categories,
    monthly_data, cash_flow_data, portfolio_analysis, trades_analysis,
    user_login, user_logout, user_signup, user_profile, csrf
)


urlpatterns = [
    path("upload/", upload, name="upload"),
    path("upload/<str:upload_id>/status/", upload_status, name="upload_status"),
    path("upload/<str:upload_id>/process/", upload_process, name="upload_process"),
    path("upload/history/", history, name="upload_history"),
    
    # Dashboard API endpoints
    path("dashboard/", dashboard, name="dashboard"),
    path("transactions/", transactions, name="transactions"),
    path("holdings/", holdings, name="holdings"),
    path("insights/", insights, name="insights"),
    path("spending-categories/", spending_categories, name="spending_categories"),
    path("monthly-data/", monthly_data, name="monthly_data"),
    path("cash-flow-data/", cash_flow_data, name="cash_flow_data"),
    path("reset/", reset_all_data, name="reset_all_data"),
    
    # Analysis endpoints
    path("portfolio-analysis/", portfolio_analysis, name="portfolio_analysis"),
    path("trades-analysis/", trades_analysis, name="trades_analysis"),
    
    # Authentication endpoints
    path("auth/csrf/", csrf, name="csrf"),
    path("auth/login/", user_login, name="user_login"),
    path("auth/logout/", user_logout, name="user_logout"),
    path("auth/signup/", user_signup, name="user_signup"),
    path("auth/profile/", user_profile, name="user_profile"),
]

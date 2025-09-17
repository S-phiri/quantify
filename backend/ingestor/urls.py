from django.urls import path
from .views import (
    upload, history, upload_status, upload_process,
    dashboard, transactions, holdings, insights, spending_categories,
    monthly_data, cash_flow_data
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
]

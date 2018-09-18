from django.urls import path
from finances import views


urlpatterns = [
    path('', views.index, name='index'),
    path('leases', views.leaseview, name='leaseview'),
    path('leases/<str:c>', views.leaseview, name='leaseview'),
    path('tenant/<int:pk>', views.TenantDetail.as_view(), name='tenantdetail'),
]

#Transaction URLs
urlpatterns += [
    path('transactions', views.transactionview, name='transactions'),
    path('transactions/all_transactions.csv', views.TransactionListView.as_view(), name='transactions-export'),
    path('transactions/edit/<int:pk>', views.TransactionUpdate.as_view(), name='edit-transaction'),
    path('transactions/create', views.TransactionCreate.as_view(), name='create-transaction'),
    path('transactions/create/tenantrent/<int:pk>/lease/<int:leasepk>/month/<int:month>/year/<int:year>', views.tenantpayment, name='create-transaction'),
    path('import', views.import_transaction_view, name='import'),
]

#hours URLs
urlpatterns += [
    path('hours', views.hourview, name='hourview'),
    path('hours/<int:inv>/paid/<int:pd>', views.hourview, name='hourview'),
    path('hours/create/', views.HourCreate.as_view(), name='create-hour'),
    path('hours/update/<int:pk>', views.HourUpdate.as_view(), name='update-hour'),
    path('hours/update/paid/<int:pk>/<int:inv>/<int:pd>', views.toggle_paid, name='toggle-paid'),
]

#Template URLS
urlpatterns += [
    path('twocolumn1.html', views.twocolumn1, name='2col1'),
    path('twocolumn2.html', views.twocolumn2, name='2col2'),
    path('onecolumn.html', views.onecolumn, name='1col'),
    path('threecolumn.html', views.threecolumn, name='3col'),
]

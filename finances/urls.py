from django.urls import path
from finances import views


urlpatterns = [
    path('', views.index, name='index'),
]

#lease URLS
urlpatterns += [
    path('leases', views.leaseview, name='leaseview'),
    path('leases/<str:c>', views.leaseview, name='leaseview'),
]

#tenant URLS
urlpatterns += [
    path('tenant', views.tenantoverview, name='tenant-overview'),
    path('tenant/<int:pk>', views.tenantdetail, name='tenant-detail'),
    path('tenant/notes/<int:pk>', views.TenantNotes.as_view(), name="tenant-notes"),
    path('tenant/edit/<int:pk>', views.TenantUpdate.as_view(), name='edit-tenant'),
    path('tenant/create', views.TenantCreate.as_view(), name='create-tenant'),
    path('tenant/deposit/create', views.DepositCreate.as_view(), name='create-deposit'),
    path('tenant/deposit/edit/<int:pk>', views.DepositUpdate.as_view(), name='edit-deposit'),
    path('tenant/initialdeposit/create/<int:pk>', views.initialdeposit, name='initial-deposit'),

]

#Transaction URLs
urlpatterns += [
    path('transactions', views.transactionview, name='transactions'),
    path('transactions/all_transactions.csv', views.TransactionListView.as_view(), name='transactions-export'),
    path('transactions/edit/<int:pk>', views.TransactionUpdate.as_view(), name='edit-transaction'),
    path('transactions/create', views.TransactionCreate.as_view(), name='create-transaction'),
    path('transactions/create/tenantrent/<int:pk>/lease/<int:leasepk>/month/<int:month>/year/<int:year>', views.tenantpayment, name='create-transaction'),
    path('transactions/dividends', views.dividends, name='dividends'),
    path('transactions/dividends/pay', views.paydividends, name="pay-dividends"),
    path('import', views.import_transaction_view, name='import'),
]

#hours URLs
urlpatterns += [
    path('hours', views.hourview, name='hourview'),
    path('hours/<int:inv>/paid/<int:pd>', views.hourview, name='hourview'),
    path('hours/create/', views.hourcreate, name='create-hour'),
    path('hours/create/<int:invpk>', views.hourcreate, name='create-hour'),
    path('hours/update/<int:pk>', views.HourUpdate.as_view(), name='update-hour'),
    path('hours/update/paid/<int:pk>/<int:inv>/<int:pd>', views.toggle_paid, name='toggle-paid'),
]

#investor URLS
urlpatterns += [
    path('investors', views.investoroverview, name="investor-overview"),
    path('investor/<int:pk>', views.investordetail, name='investor-detail'),
    path('investor/edit/hourlyrate/<int:pk>', views.InvestorUpdate.as_view(), name='edit-hourly-rate'),
]

#Template URLS
urlpatterns += [
    path('twocolumn1.html', views.twocolumn1, name='2col1'),
    path('twocolumn2.html', views.twocolumn2, name='2col2'),
    path('onecolumn.html', views.onecolumn, name='1col'),
    path('threecolumn.html', views.threecolumn, name='3col'),
]

#Asset URLs
urlpatterns += [
    path('assets', views.assetoverview, name='asset-overview'),
    path('assets/<int:pk>', views.assetdetail, name='asset-detail'),
    path('assets/create/', views.AssetCreate.as_view(), name='create-asset'),
    path('assets/valueupdate/', views.AssetValueCreate.as_view(), name='asset-value-update'),
    path('assets/update/<int:pk>', views.AssetUpdate.as_view(), name='update-asset'),
]

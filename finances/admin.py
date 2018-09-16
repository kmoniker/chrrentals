from django.contrib import admin
from .models import *
# Register your models here.

# admin.site.register(Asset)
admin.site.register(Hour)
admin.site.register(Investor)
admin.site.register(Deposit)
# admin.site.register(Property)
# admin.site.register(Lease)
# admin.site.register(Tenant)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'bank_posted_date', 'pretty_amount','person', 'notes')
    list_filter = ('date', 'bank_posted_date', 'person', 'tenant', 'investor')
    fields = (('date','bank_posted_date'),('amount', 'out_flow'), ('person','investor', 'tenant'), 'notes',)
    ordering= ('-date',)


class LeaseInline(admin.TabularInline):
    model = Lease

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    inlines = [LeaseInline,]

class TenantInline(admin.TabularInline):
    model=Lease.tenant_set.through

@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    list_display = ('property', 'lease_start', 'lease_end', 'rent_due')
    ordering=('-lease_start',)
    inlines = [TenantInline,]

class TransactionInline(admin.TabularInline):
    model = Transaction

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    inlines = [TransactionInline,]
    ordering=('name',)

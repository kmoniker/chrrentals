from django.contrib import admin
from .models import *
# Register your models here.

# admin.site.register(Asset)
admin.site.register(Hour)
# admin.site.register(Investor)
admin.site.register(Deposit)
# admin.site.register(Lease)
# admin.site.register(Tenant)
admin.site.register(Dividend)

class LeaseInline(admin.TabularInline):
    model = Lease

class DepositInline(admin.TabularInline):
    model = Deposit

class AssetValueInline(admin.TabularInline):
    model = AssetValue

class TenantInline(admin.TabularInline):
    model=Lease.tenant_set.through

class TransactionInline(admin.TabularInline):
    model = Transaction

@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    inlines = [TransactionInline,]

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    inlines = [LeaseInline, AssetValueInline,]
    list_display = ('name','get_value',)

@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    list_display = ('property', 'lease_start', 'lease_end', 'rent_due')
    ordering=('-lease_start',)
    inlines = [TenantInline,]

def make_assign_to_property_action(asset):
    def assign_to_property(modeladmin, request, queryset):
        for transaction in queryset:
            transaction.assign_property(asset)
            #message_user.info(request, "Transaction {0} assigned to {1}".format(transaction.id,asset.name))
            transaction.save()
            
    assign_to_property.short_description = "Assign to {0}".format(asset.name)
    assign_to_property.__name__ = 'assign_to_user_{0}'.format(asset.id)

    return assign_to_property

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'bank_posted_date', 'pretty_amount','person', 'property', 'notes')
    list_filter = ('date', 'bank_posted_date', 'person', 'tenant', 'investor', 'property')
    fields = (('date','bank_posted_date'),('amount', 'out_flow'), ('person','investor', 'tenant','property'), 'notes',)
    ordering= ('-date',)

    def get_actions(self, request):
        actions = super(TransactionAdmin, self).get_actions(request)
        assets = Asset.objects.filter(property=True).order_by('name')
        for asset in assets:
            action = make_assign_to_property_action(asset)
            actions[action.__name__] = (action,
                                        action.__name__,
                                        action.short_description)

        return actions


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    inlines = [DepositInline,]
    ordering=('name',)
    list_display = ('name', 'get_current_lease', 'active', 'get_deposit_value')

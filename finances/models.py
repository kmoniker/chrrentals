from django.db import models
from datetime import datetime
from django.urls import reverse
import calendar
from django.db.models import Sum

# Create your models here.

class Transaction(models.Model):
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    date = models.DateField(null=True)
    bank_posted_date = models.DateField(null=True, blank=True)
    person = models.CharField(max_length=200, help_text="The other party in the transaction.", null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    out_flow = models.BooleanField()
    investor = models.ForeignKey('Investor', on_delete=models.SET_NULL, null=True, blank=True)
    tenant = models.ForeignKey('Tenant', on_delete=models.SET_NULL, null=True, blank=True)

    def pretty_amount(self):
        if self.out_flow == False:
            return "$%s" % self.amount
        else:
            return "-$%s" % self.amount
    pretty_amount.short_description="amount"

    def pretty_date(self):
        return self.date.strftime("%Y-%m-%d")

    def pretty_bank_date(self):
        if self.bank_posted_date == None:
            return None
        else:
            return self.bank_posted_date.strftime("%Y-%m-%d")

    def get_edit_url(self):
         return reverse('edit-transaction', args=[str(self.id)])

    def get_absolute_url(self):
        return reverse('transactions')

    def __str__(self):
        return "%s (%s)" % (self.amount, self.date)

class Investor(models.Model):
    name = models.CharField(max_length=200)
    percentage = models.FloatField(default=0)

    def pretty_total_invested(self):
        transactions = self.transaction_set.all()
        total = 0

        for t in transactions:
            if t.out_flow != True:
                total += t.amount
        return "${:,.2f}".format(total)

    def total_invested(self):
        transactions = self.transaction_set.all()
        total = 0

        for t in transactions:
            if t.out_flow != True:
                total += t.amount
        return total

    def total_received(self):
        transactions = self.transaction_set.all()
        total = 0

        for t in transactions:
            if t.out_flow != False:
                total += t.amount
        return "${:,.2f}".format(total)

    def pretty_percent(self):
        p = self.percentage*100
        return "{:.2f}%".format(p)

    def get_equity(self):
        assets = Asset.objects.all()
        total=0

        for a in assets:
            val = a.get_value()
            total += a.get_value()
        t = self.percentage*float(total)
        return "${:,.2f}".format(t)

    def get_absolute_url(self):
         return reverse('investor-detail', args=[str(self.id)])

    def __str__(self):
        return self.name

class Asset(models.Model):
    name = models.CharField(max_length=200)
    property = models.BooleanField(default=True)

    def get_value(self, str=False):
        now = datetime.now().astimezone()
        lst = self.assetvalue_set.all()
        dates=[]
        for v in lst:
            dates.append(v.date)
        if len(dates) == 0:
            value = 0
        else:
            youngest = max(dt for dt in dates if dt < now)
            assetvalue = self.assetvalue_set.filter(date=youngest)[0]
            value = assetvalue.value
        if str == True:
            value = "${:,.2f}".format(value)
        return value

    def __str__(self):
        return self.name

class AssetValue(models.Model):
    asset = models.ForeignKey('asset', on_delete=models.SET_NULL, null=True, blank=True)
    value = models.DecimalField(max_digits=8, decimal_places=2)
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "$%s (%s)" % (self.value, self.date.strftime("%m/%d/%Y"))

class Lease(models.Model):
    property = models.ForeignKey('Asset',  on_delete=models.SET_NULL, null=True)
    lease_start = models.DateField()
    lease_end = models.DateField()
    rent_due = models.DecimalField(max_digits=8, decimal_places=2)
    utilities_due = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return "%s (%s to %s)" % (self.property.name, self.lease_start.year, self.lease_end.year)

    def required_deposit(self):
        return self.rent_due*2

    def monthly_payment(self):
        return self.rent_due+self.utilities_due

    def is_current(self):
        now = datetime.today().date()
        end = self.lease_end
        if end > now:
            return True
        else:
            return False

    def get_months(self):
        months = []
        startmonth = self.lease_start.month
        startyear = self.lease_start.year
        endmonth = self.lease_end.month
        mnthstring = "%s %s" % (calendar.month_abbr[startmonth], startyear)
        #months.append(mnthstring) This appends the first month, august onto the string
        while startmonth+1 != endmonth:
            if startmonth == 12:
                startmonth = 1
                startyear += 1
            else:
                startmonth +=1
            mnthstring = "%s %s" % (calendar.month_abbr[startmonth], startyear)
            months.append(mnthstring)
        if startmonth == 12:
            startmonth = 1
            startyear += 1
        else:
            startmonth +=1
        mnthstring = "%s %s" % (calendar.month_abbr[startmonth], startyear)
        months.append(mnthstring)

        return months
    def get_months_comp(self):
        months_comp = []
        startmonth = self.lease_start.month+1
        startyear = self.lease_start.year
        endmonth = self.lease_end.month
        while startmonth != endmonth:
            mnthstringcomp = "%s %s" % (calendar.month_name[startmonth], startyear)
            months_comp.append(mnthstringcomp)
            if startmonth == 12:
             startmonth = 1
             startyear += 1
            else:
             startmonth +=1
        mnthstringcomp = "%s %s" % (calendar.month_name[startmonth], startyear)
        months_comp.append(mnthstringcomp)

        return months_comp

    def get_absolute_url(self):
        url =  "%s#%s" % (reverse('leaseview'), self.pk)
        print(url)
        return url

class Hour(models.Model):
    name = models.ForeignKey('Investor', on_delete=models.SET_NULL, null=True)
    date = models.DateField()
    hours = models.IntegerField()
    work = models.CharField(max_length=400, help_text="what were you doing?")
    paid = models.BooleanField(default=False)

    def __str__(self):
        return "%s - %s (%s)" % (self.hours, self.name, self.date)

    def get_absolute_url(self):
        return reverse('hourview')

    def get_edit_url(self):
         return reverse('update-hour', args=[str(self.id)])


class Tenant(models.Model):
    name = models.CharField(max_length=200)
    lease = models.ManyToManyField('Lease', blank=True)
    active = models.BooleanField(default=True, help_text="Is this tenant on an active lease?")
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    def get_edit_url(self):
         return reverse('update-hour', args=[str(self.id)])

    def get_absolute_url(self):
         return reverse('tenantdetail', args=[str(self.id)])

    def get_current_lease(self):
        return self.lease.latest('lease_start')

    def get_rent_payment(self, month, year):
        rentstring = "%s %s Rent" % (calendar.month_name[month], year)
        t = self.transaction_set.filter(notes__icontains=rentstring).values('date')

        if len(t) == 0:
            return {"result":"False",
                    "pk":self.pk,
                    "month":month,
                    "year":year}
        elif len(t) == 1:
            return t[0]['date']
        else:
            return "error"

    def get_rent_payments(self, smonth=1, syear=2018, nmonth=12, nyear=2018):
        payments = []
        # pmt = self.get_rent_payment(smonth, syear)  THESE LINES of code add the first month (august) on
        # payments.append(pmt)
        while nmonth != smonth or nyear != syear:
            if smonth == 12:
                smonth = 1
                syear += 1
            else:
                smonth +=1
            pmt = self.get_rent_payment(smonth, syear)
            payments.append(pmt)
        return(payments)

    def get_deposit_value(self):
        deposit_value = self.deposit_set.aggregate(Sum('amount'))
        return deposit_value['amount__sum']

class Deposit(models.Model):
    tenant = models.ForeignKey('Tenant', on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2)

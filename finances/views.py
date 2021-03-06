from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views import generic
from django.db.models import Sum
from django.http import JsonResponse
import calendar
import csv
from decimal import Decimal
from datetime import datetime, timedelta

from .models import *
from .forms import *
# Create your views here.
def get_data(request):
    properties = Asset.objects.filter(property=True)
    labels = []
    values = []
    for p in properties:
        labels.append(p.name)
        values.append(p.get_value())

    data = {
        'labels':labels,
        'values':values,
    }
    return JsonResponse(data)

def chart_test(request):
    return render(
        request,
        'chart.html',
        context = {
            'labels':['lab1','lab2'],
            'values':[1,2]

        }
    )

def index(request):

    return render(
        request,
        'index.html',
        context = {
        }
    )

def leaseview(request, c='current'):
    leaselst = Lease.objects.all()

    current = []
    past = []
    for l in leaselst:
        if l.is_current():
            current.append(l)
        else:
            past.append(l)

    lease_dict = {}
    if c == 'current':
        for l in current:
            lease_dict[l] = {}
    else:
        for l in past:
            lease_dict[l] = {}

    for l in lease_dict:
        lst = l.tenant_set.all()
        for t in lst:
            lease_dict[l][t] = t.get_rent_payments(l.lease_start.month, l.lease_start.year, l.lease_end.month, l.lease_end.year)


    return render(
        request,
        'leaseview.html',
        context={"current":current, "past":past, "lease_dict":lease_dict}
    )

def hourview(request, inv=0, pd=0):
    investors = Investor.objects.all().order_by("name")

    if inv !=0:
        i = Investor.objects.get(pk=inv)
        if pd==0:
            hours = i.hour_set.all().order_by('-date')
        elif pd==1:
            hours = i.hour_set.filter(paid=True).order_by('-date')
        else:
            hours = i.hour_set.filter(paid=False).order_by('-date')
    else:
        if pd==0:
            hours = Hour.objects.all().order_by('-date')
        elif pd==1:
            hours = Hour.objects.filter(paid=True).order_by('-date')
        else:
            hours = Hour.objects.filter(paid=False).order_by('-date')


    total_hours = hours.aggregate(Sum('hours'))
    total_hours = total_hours['hours__sum']
    total_value = 0
    for h in hours:
        total_value += h.hours*h.name.rate

    return render(
    request,
    'hours.html',
    context = {
            "investors":investors,
            "hours":hours,
            "inv":inv,
            "pd":pd,
            "total_hours":total_hours,
            "value":total_value,
            }
    )

def hourcreate(request, invpk=0):
     # If this is a POST request then process the Form data
    if request.method == 'POST':
        # Create a form instance and populate it with data from the request (binding):
        form = HourForm(request.POST)
        # Check if the form is valid:
        if form.is_valid():
            print(form.cleaned_data)
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            h = Hour(
                    name = form.cleaned_data['name'],
                    date = form.cleaned_data['date'],
                    hours = form.cleaned_data['hours'],
                    work = form.cleaned_data['work'],
                    paid = form.cleaned_data['paid'],
                    rate = form.cleaned_data['name'].rate
                    )
            h.save()


            # redirect to a new URL:
            return redirect(reverse('investor-detail', args=[str(form.cleaned_data['name'].pk)]))

    # If this is a GET (or any other method) create the default form.
    else:
        if invpk == 0:
            initial_investor = None
        else:
            initial_investor = Investor.objects.get(pk=invpk)
        form = HourForm(initial={
                                    'name': initial_investor,
                                    'date': datetime.today(),
                                    })

    return render(
        request,
        'finances/generic_form.html',
        context = {'form':form}
        )


class HourUpdate(UpdateView):
    model = Hour
    form_class = HourForm

def toggle_paid(request, pk, inv, pd):
    hour = Hour.objects.get(pk=pk)
    paid = not hour.paid
    hour.paid = paid
    hour.save()
    return redirect('hourview', inv=inv, pd=pd)

def tenantpayment(request, pk, leasepk, year, month):
    tenant = Tenant.objects.get(pk = pk)
    property = tenant.lease.get(pk=leasepk).property
    amount = tenant.lease.get(pk=leasepk).monthly_payment()
    notes = "%s %s Rent" % (calendar.month_name[month], year)

     # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = TransactionForm(request.POST)
        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            date = form.cleaned_data['date']
            bank_posted_date = form.cleaned_data['bank_posted_date']
            amount = form.cleaned_data["amount"]
            out_flow = form.cleaned_data["out_flow"]
            person = form.cleaned_data["person"]
            investor = form.cleaned_data["investor"]
            tenant = form.cleaned_data["tenant"]
            notes = form.cleaned_data["notes"]
            t = Transaction(
                amount=amount,
                date=date,
                bank_posted_date=bank_posted_date,
                person=person,
                notes=notes,
                out_flow=out_flow,
                tenant=tenant,
                property=form.cleaned_data['property'])
            t.save()


            # redirect to a new URL:
            return redirect("%s#%s" % (reverse('leaseview'), leasepk))

    # If this is a GET (or any other method) create the default form.
    else:
        form = TransactionForm(initial={
                                    'date': "%s-%s-01" % (year, month),
                                    'bank_posted_date': "%s-%s-07" % (year, month),
                                    'amount': amount,
                                    'person': tenant.name,
                                    'tenant': tenant,
                                    'property': property,
                                    'notes': notes,
                                    })

    return render(
        request,
        'finances/transaction_form.html',
        context = {'form':form, "tenant":tenant}
        )

def initialdeposit(request, pk):
    tenant = Tenant.objects.get(pk = pk)
    lease = tenant.get_current_lease()
    amount = lease.required_deposit()
    notes = "Initial Deposit for %s" % (lease)

     # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = InitialDepositForm(request.POST)
        # Check if the form is valid:
        if form.is_valid():
            print(form.cleaned_data)
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            t = Transaction(
                amount=form.cleaned_data['amount'],
                date=form.cleaned_data['date'],
                bank_posted_date=form.cleaned_data['bank_posted_date'],
                person=tenant.name,
                notes=form.cleaned_data['notes'],
                out_flow=False,
                tenant=form.cleaned_data['tenant'])
            t.save()
            d = Deposit(
                tenant = form.cleaned_data['tenant'],
                amount = form.cleaned_data['amount'],
                date = form.cleaned_data['date'],
                notes = form.cleaned_data['notes'])
            d.save()

            # redirect to a new URL:
            return redirect("%s#%s" % (reverse('leaseview'), lease.pk))

    # If this is a GET (or any other method) create the default form.
    else:
        form = InitialDepositForm(initial={
                                    'date': datetime.today(),
                                    'bank_posted_date': None,
                                    'amount': amount,
                                    'tenant': tenant,
                                    'notes': notes,
                                    })

    return render(
        request,
        'finances/generic_form.html',
        context = {'form':form, "tenant":tenant}
        )



class TenantDetail(generic.DetailView):
    model=Tenant
    fields = "__all__"

def tenantdetail(request, pk):
    tenant = Tenant.objects.get(pk=pk)
    menu = Tenant.objects.all().order_by('-active', 'name')
    transactions = tenant.transaction_set.all().order_by("-date")
    deposits = tenant.deposit_set.all().order_by('-date')
    return render(
        request,
        'finances/tenant_detail.html',
        context = {
                    "menu":menu,
                    "tenant":tenant,
                    "transaction_set":transactions,
                    "deposit_set":deposits,
                    "pk":pk
                    }
    )

def tenantoverview(request):
    menu = Tenant.objects.all().order_by('-active', 'name')
    transactions = Transaction.objects.exclude(tenant=None).order_by("-date")
    leases = Lease.objects.all()
    deposits = Deposit.objects.all().order_by('-date')
    deposit_value = Deposit.objects.aggregate(Sum("amount"))['amount__sum']

    try:
        deposit_value = "${:,.2f}".format(deposit_value)
    except TypeError:
        deposit_value = None
    lease_list = []
    for l in leases:
        if l.is_current():
            lease_list.append(l)

    tenant = {
                "name":"Tenant Overview",
                "get_deposit_value":deposit_value,
    }

    return render(
        request,
        'finances/tenant_detail.html',
        context = {
                    "menu":menu,
                    "tenant":tenant,
                    "transaction_set":transactions,
                    "lease_list":lease_list,
                    "deposit_set":deposits,
                    }
    )

class TenantNotes(UpdateView):
    model = Tenant
    fields = ("notes",)
    template_name = "finances/generic_form.html"

class TenantUpdate(UpdateView):
    model = Tenant
    fields = "__all__"
    template_name = "finances/generic_form.html"

class TenantCreate(CreateView):
    model = Tenant
    fields = "__all__"
    template_name = "finances/generic_form.html"

class DepositUpdate(UpdateView):
    model = Deposit
    fields = "__all__"
    template_name = "finances/generic_form.html"

class DepositCreate(CreateView):
    model = Deposit
    fields = "__all__"
    template_name = "finances/generic_form.html"

class DividendCreate(CreateView):
    model = Dividend
    fields = "__all__"
    template_name = "finances/generic_form.html"

class TransactionCreate(CreateView):
    model = Transaction
    form_class = TransactionForm
    initial={
            'date': datetime.today(),
            }

class TransactionUpdate(UpdateView):
    model = Transaction
    form_class = TransactionForm

class TransactionListView(generic.ListView): #For exporting Transactions
    model = Transaction
    context_object_name = "transaction_list"
    template_name = 'all_transactions.csv'
    content_type = 'text/csv'

    def get_queryset(self) :
        return Transaction.objects.extra(select={"order_date":"COALESCE(bank_posted_date, date)"}, order_by=["-order_date", "-date"])

def transactionview(request):
    transaction_list = Transaction.objects.extra(select={"order_date":"COALESCE(bank_posted_date, date)"}, order_by=["-order_date", "-date"])

    into_bank = Transaction.objects.filter(out_flow=False).exclude(bank_posted_date=None).aggregate(Sum('amount'))
    outof_bank = Transaction.objects.filter(out_flow=True).exclude(bank_posted_date=None).aggregate(Sum('amount'))

    try:
        in_bank = into_bank['amount__sum']-outof_bank['amount__sum']
    except TypeError:
        in_bank = 0
        print("inbank TYPE ERROR")

    try:
        last_bank_update = Transaction.objects.exclude(bank_posted_date=None).order_by('-bank_posted_date').first().bank_posted_date
    except:
        last_bank_update = "error"
        print("lastbankupdate ERROR")

    try:
        value = Asset.objects.get(name="UCCU Bank Account").get_value()
    except:
        value = "error"
        print("value ERROR")


    if value == in_bank:
        in_bank_color = "green"
    elif value == "error":
        in_bank_color = "blue"
    else:
        in_bank_color = "red"

    return render(
        request,
        'finances/transaction_list.html',
        context = {
                    'transaction_list':transaction_list,
                    "in_bank": "${:,.2f}".format(in_bank),
                    "last_bank_update":last_bank_update,
                    "in_bank_color":in_bank_color,
                    }
    )

def import_transaction_view(request):
    with open('upload_transactions.csv') as f:
            reader = csv.reader(f)
            firstrow=True
            for row in reader:
                if firstrow==True:
                    firstrow=False
                    continue
                amt = row[3].replace("$", "")
                amt = amt.replace(",", "")
                amt = amt.replace("(", "-")
                amt = amt.replace(")", "")
                amt = Decimal(amt)
                if amt < 0:
                    o_f = True
                    amt = abs(amt)
                else:
                    o_f = False

                if row[2]=="None":
                    bpd=None
                else:
                    bpd=datetime.strptime(row[2],"%m/%d/%Y").strftime("%Y-%m-%d")

                date = datetime.strptime(row[1],"%m/%d/%Y").strftime("%Y-%m-%d")

                if row[7] != "None":
                    tenant, result = Tenant.objects.get_or_create(name=row[7], defaults={'current':False})
                    print(tenant, result)
                else:
                    tenant = None

                if row[6] != "None":
                    investor, result = Investor.objects.get_or_create(name=row[6])
                    print(investor, result)
                else:
                    investor = None

                trans, created = Transaction.objects.update_or_create(
                    pk = row[0],
                    date = date,
                    bank_posted_date = bpd,
                    amount = amt,
                    person = row[4],
                    notes = row[5],
                    out_flow = o_f,
                    defaults = {
                    'investor':investor,
                    'tenant':tenant,}
                    )

                print(trans, created)
                # creates a tuple of the new object or
                # current object and a boolean of if it was created
    return redirect('index')

def investordetail(request, pk):
    investor = Investor.objects.get(pk=pk)
    menu = Investor.objects.all()
    transactions = investor.transaction_set.all().order_by("-date")
    hours = investor.hour_set.all().order_by('-date')
    return render(
        request,
        'finances/investor_detail.html',
        context = {
                    "pk":pk,
                    "menu":menu,
                    "investor":investor,
                    "transaction_set":transactions,
                    "hours":hours,
                    }
    )

def investoroverview(request):
    menu = Investor.objects.all()

    assets = Asset.objects.all()
    total=0
    for a in assets:
        val = a.get_value()
        total += a.get_value()
    equity = "${:,.2f}".format(total)
    print(equity)
    transactions = Transaction.objects.exclude(investor=None).order_by("-date")

    hours = Hour.objects.all().order_by('-date')

    investor = {
                "name":"Investor Overview",
                "pretty_percent":"100.00%",
                "get_pretty_equity": equity,
    }

    return render(
        request,
        'finances/investor_detail.html',
        context = {
                    "menu":menu,
                    "investor":investor,
                    "transaction_set":transactions,
                    "hours":hours,
                    }
    )

class InvestorUpdate(UpdateView):
    model = Investor
    form_class = HourlyRateForm
    template_name = 'finances/generic_form.html'

def dividends(request):
    investors = Investor.objects.exclude(percentage=0)
    t_percent = Investor.objects.aggregate(Sum('percentage'))
    t_out = 0
    for i in investors:
        t_out += i.get_dividend()
    total = {
            "percent":"{}%".format(t_percent['percentage__sum']*100),
            "total_out":"${:,.2f}".format(t_out)
            }

    transaction_set = Transaction.objects.filter(notes__icontains="dividend").exclude(investor=None)
    latest_transaction = transaction_set.latest('date')

    date = datetime.today()
    notes = "%s %s Dividend" % (calendar.month_name[date.month-1], date.year)

    return render(
        request,
        'dividends.html',
        context = {
                "investors":investors,
                "total":total,
                "last_dividend":latest_transaction,
                "notes":notes
        }
    )

def paydividends(request):
    investor_lst = Investor.objects.exclude(percentage=0)
    date = datetime.today()
    notes = "%s %s Dividend" % (calendar.month_name[date.month-1], date.year)
    for i in investor_lst:
        Transaction.objects.create(date = date,
            bank_posted_date = None,
            amount = i.get_dividend(),
            person = i.name,
            notes = notes,
            out_flow = True,
            tenant = None,
            investor = i
            )

    return redirect('investor-overview')

def assetoverview(request):
    assets = Asset.objects.all()

    total=0
    for a in assets:
        val = a.get_value()
        total += a.get_value()
    get_value = "${:,.2f}".format(total)

    property_set = Asset.objects.filter(property=True)
    non_property_set = Asset.objects.filter(property=False)

    asset = {
                "name":"Asset Overview",
    }

    inflows = Transaction.objects.filter(out_flow=False)
    inflow_sum = 0
    for i in inflows:
        inflow_sum += i.amount

    outflows = Transaction.objects.filter(out_flow=True)
    outflow_sum = 0
    for i in outflows:
        outflow_sum += i.amount

    net = inflow_sum-outflow_sum

    return render(
        request,
        'finances/asset_overview.html',
        context = {
                    "menu":assets,
                    "asset":asset,
                    "property_set":property_set,
                    "non_property_set":non_property_set,
                    "get_value":get_value,
                    "inflow_sum":"${:,.2f}".format(inflow_sum),
                    "outflow_sum":"${:,.2f}".format(outflow_sum),
                    "net":"${:,.2f}".format(net),

                  }
    )

def assetdetail(request, pk):
    asset = Asset.objects.get(pk=pk)
    menu = Asset.objects.all()
    value_set = AssetValue.objects.filter(asset=pk).order_by("-date")
    if asset.property==True:
        transaction_set = Transaction.objects.filter(property=pk).order_by("-date")
    else: transaction_set=False

    return render(
        request,
        'finances/asset_detail.html',
        context = {
                    "pk":pk,
                    "menu":menu,
                    "asset":asset,
                    "get_value":asset.get_value(True),
                    "get_expenses":asset.get_transaction("expense"),
                    "get_inflow":asset.get_transaction("inflow"),
                    "get_net":asset.get_net(),
                    "value_set":value_set,
                    "transaction_set":transaction_set,
                    }
    )


class AssetUpdate(UpdateView):
    model = Asset
    fields = "__all__"
    template_name = "finances/generic_form.html"

class AssetCreate(CreateView):
    model = Asset
    fields = "__all__"
    template_name = "finances/generic_form.html"

class AssetValueCreate(CreateView):
    model = AssetValue
    fields = "__all__"
    template_name = "finances/generic_form.html"

# template VIEWS
def twocolumn1(request):
    return render(
        request,
        'twocolumn1.html',
        context = {}
    )

def twocolumn2(request):
    return render(
        request,
        'twocolumn2.html',
        context = {}
    )

def onecolumn(request):
    return render(
        request,
        'onecolumn.html',
        context = {}
    )

def threecolumn(request):
    return render(
        request,
        'threecolumn.html',
        context = {}
    )

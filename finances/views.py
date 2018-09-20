from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views import generic
from django.db.models import Sum
import calendar
import csv
from decimal import Decimal
from datetime import datetime, timedelta

from .models import *
from .forms import *
# Create your views here.

def index(request):
    return render(
        request,
        'index.html',
        context = {}
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
    return render(
    request,
    'hours.html',
    context = {"investors":investors, "hours":hours, "inv":inv, "pd":pd, "total_hours":total_hours}
    )

class HourCreate(CreateView):
    model = Hour
    form_class = HourForm
    initial={
            'date': datetime.today(),
            }

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
            person = tenant.name
            out_flow = False
            t = Transaction(
                amount=amount,
                date=date,
                bank_posted_date=bank_posted_date,
                person=person,
                notes=notes,
                out_flow=out_flow,
                tenant=tenant)
            t.save()


            # redirect to a new URL:
            return redirect("%s#%s" % (reverse('leaseview'), leasepk))

    # If this is a GET (or any other method) create the default form.
    else:
        form = TransactionForm(initial={
                                    'date': "%s-%s-01" % (year, month),
                                    'bank_posted_date': "%s-%s-07" % (year, month),
                                    'amount': amount,
                                    'tenant': tenant,
                                    'notes': notes,
                                    })

    return render(
        request,
        'finances/transaction_form.html',
        context = {'form':form, "tenant":tenant}
        )

class TenantDetail(generic.DetailView):
    model=Tenant
    fields = "__all__"

def tenantdetail(request, pk):
    tenant = Tenant.objects.get(pk=pk)
    menu = Tenant.objects.all().order_by('-active', 'name')
    transactions = tenant.transaction_set.all().order_by("-date")
    return render(
        request,
        'finances/tenant_detail.html',
        context = {
                    "menu":menu,
                    "tenant":tenant,
                    "transaction_set":transactions,
                    "pk":pk
                    }
    )

def tenantoverview(request):
    menu = Tenant.objects.all().order_by('-active', 'name')
    transactions = Transaction.objects.exclude(tenant=None).order_by("-date")
    leases = Lease.objects.all()
    lease_list = []
    for l in leases:
        if l.is_current():
            lease_list.append(l)

    tenant = {
                "name":"Overview",
    }

    return render(
        request,
        'finances/tenant_detail.html',
        context = {
                    "menu":menu,
                    "tenant":tenant,
                    "transaction_set":transactions,
                    "lease_list":lease_list,
                    }
    )


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

    in_bank = into_bank['amount__sum']-outof_bank['amount__sum']

    last_bank_update = Transaction.objects.exclude(bank_posted_date=None).order_by('-bank_posted_date').first().bank_posted_date

    try:
        value = Asset.objects.get(name="UCCU Bank Account").get_value()
    except:
        value = "error"

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

    transactions = Transaction.objects.exclude(investor=None).order_by("-date")

    hours = Hour.objects.all().order_by('-date')

    investor = {
                "name":"Overview",
                "pretty_percent":"100.00%",
                "get_equity": equity,
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

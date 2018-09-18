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
    print(total_hours)
    total_hours = total_hours['hours__sum']
    return render(
    request,
    'hours.html',
    context = {"investors":investors, "hours":hours, "inv":inv, "pd":pd, "total_hours":total_hours}
    )

class HourCreate(CreateView):
    model = Hour
    fields = ('name', 'date', 'hours', 'work')

class HourUpdate(UpdateView):
    model = Hour
    fields = ('name', 'date', 'hours', 'work')

def toggle_paid(request, pk, inv, pd):
    hour = Hour.objects.get(pk=pk)
    paid = not hour.paid
    hour.paid = paid
    hour.save()
    return redirect('hourview', inv=inv, pd=pd)

class TransactionCreate(CreateView):
    model = Transaction
    fields = "__all__"

def tenantpayment(request, pk, leasepk, year, month):
    tenant = Tenant.objects.get(pk = pk)
    amount = tenant.lease.get(pk=leasepk).monthly_payment()
    notes = "%s %s Rent" % (calendar.month_name[month], year)

     # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RentPaidForm(request.POST)
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
        form = RentPaidForm(initial={
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

class TransactionListView(generic.ListView):
    model = Transaction
    context_object_name = "transaction_list"
    template_name = 'all_transactions.csv'
    content_type = 'text/csv'

    def get_queryset(self) :
        return Transaction.objects.extra(select={"order_date":"COALESCE(bank_posted_date, date)"}, order_by=["-order_date", "-date"])

def transactionview(request):
    transaction_list = Transaction.objects.extra(select={"order_date":"COALESCE(bank_posted_date, date)"}, order_by=["-order_date", "-date"])

    return render(
        request,
        'finances/transaction_list.html',
        context = {'transaction_list':transaction_list}
    )

def import_transaction_view(request):
    with open('upload_transactions.csv') as f:
            reader = csv.reader(f)
            firstrow=True
            for row in reader:
                if firstrow==True:
                    firstrow=False
                    continue
                amt = row[2].replace("$", "")
                amt = amt.replace(",", "")
                amt = amt.replace("(", "-")
                amt = amt.replace(")", "")
                amt = Decimal(amt)
                if amt < 0:
                    o_f = True
                    amt = abs(amt)
                else:
                    o_f = False

                if row[1]=="None":
                    bpd=None
                else:
                    bpd=datetime.strptime(row[1],"%m/%d/%Y").strftime("%Y-%m-%d")
                print(bpd)

                date = datetime.strptime(row[0],"%m/%d/%Y").strftime("%Y-%m-%d")

                if row[6] != "None":
                    tenant, result = Tenant.objects.get_or_create(name=row[6], defaults={'current':False})
                    print(tenant, result)
                else:
                    tenant = None

                if row[5] != "None":
                    investor, result = Investor.objects.get_or_create(name=row[5])
                    print(investor, result)
                else:
                    investor = None

                trans, created = Transaction.objects.update_or_create(
                    date = date,
                    bank_posted_date = bpd,
                    amount = amt,
                    person = row[3],
                    notes = row[4],
                    out_flow = o_f,
                    defaults = {
                    'investment':investor,
                    'tenant':tenant,}
                    )

                print(trans, created)
                # creates a tuple of the new object or
                # current object and a boolean of if it was created
    return redirect('index')

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

from django import forms
from .models import Transaction, Hour, Tenant, Investor, Asset
from datetime import datetime

class InitialDepositForm(forms.Form):
    amount = forms.DecimalField(max_digits=8, decimal_places=2)
    date = forms.DateField(widget = forms.SelectDateWidget(years=range(datetime.today().year-2, datetime.today().year+2)))
    bank_posted_date = forms.DateField(required=False, widget=forms.SelectDateWidget(years=range(datetime.today().year-2, datetime.today().year+2)))
    tenant = forms.ModelChoiceField(queryset=Tenant.objects.all())
    notes = forms.CharField(widget=forms.Textarea)

class TransactionForm(forms.ModelForm):
    date = forms.DateField(widget = forms.SelectDateWidget(years=range(datetime.today().year-2, datetime.today().year+2)))
    bank_posted_date = forms.DateField(required=False, widget=forms.SelectDateWidget(years=range(datetime.today().year-2, datetime.today().year+2)))

    class Meta:
        model = Transaction
        fields = ('date', 'bank_posted_date', 'amount', 'out_flow', 'person', 'investor', 'tenant', 'property', 'notes')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['property'].queryset = Asset.objects.filter(property=True)

class HourForm(forms.ModelForm):
    date = forms.DateField(widget = forms.SelectDateWidget(years=range(datetime.today().year-2, datetime.today().year+2)))
    class Meta:
        model = Hour
        fields = ("name", "date", "hours", "work", "paid")

class HourlyRateForm(forms.ModelForm):
    class Meta:
        model = Investor
        fields = ('rate',)

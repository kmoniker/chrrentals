from django import forms
from .models import Transaction
from datetime import datetime

class RentPaidForm(forms.ModelForm):
    date = forms.DateField(widget = forms.SelectDateWidget(years=range(2010, datetime.today().year+2)))
    bank_posted_date = forms.DateField(widget = forms.SelectDateWidget(years=range(2010, datetime.today().year+2)))
    class Meta:
        model = Transaction
        fields = ('date','bank_posted_date','amount', 'tenant', 'notes')


class NewInvestmentForm(forms.Form):
    amount = forms.DecimalField(max_digits=8, decimal_places=2)
    date = forms.DateField()

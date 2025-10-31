from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import Route, Bid


class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = [
            'origin_city', 'origin_country', 'origin_lat', 'origin_lng',
            'destination_city', 'destination_country', 'destination_lat', 'destination_lng',
            'cargo_type', 'weight', 'volume', 'price',
            'pickup_date', 'delivery_date', 'description'
        ]
        widgets = {
            'origin_city': forms.TextInput(attrs={'class': 'form-control'}),
            'origin_country': forms.TextInput(attrs={'class': 'form-control'}),
            'origin_lat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'origin_lng': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'destination_city': forms.TextInput(attrs={'class': 'form-control'}),
            'destination_country': forms.TextInput(attrs={'class': 'form-control'}),
            'destination_lat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'destination_lng': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'cargo_type': forms.TextInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'volume': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pickup_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'delivery_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('origin_city', css_class='col-md-6'),
                Column('origin_country', css_class='col-md-6'),
            ),
            Row(
                Column('origin_lat', css_class='col-md-6'),
                Column('origin_lng', css_class='col-md-6'),
            ),
            Row(
                Column('destination_city', css_class='col-md-6'),
                Column('destination_country', css_class='col-md-6'),
            ),
            Row(
                Column('destination_lat', css_class='col-md-6'),
                Column('destination_lng', css_class='col-md-6'),
            ),
            Row(
                Column('cargo_type', css_class='col-md-6'),
                Column('price', css_class='col-md-6'),
            ),
            Row(
                Column('weight', css_class='col-md-6'),
                Column('volume', css_class='col-md-6'),
            ),
            Row(
                Column('pickup_date', css_class='col-md-6'),
                Column('delivery_date', css_class='col-md-6'),
            ),
            'description',
            Submit('submit', 'Створити маршрут', css_class='btn btn-primary w-100 mt-3')
        )


class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['proposed_price', 'estimated_delivery', 'message']
        widgets = {
            'proposed_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estimated_delivery': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'proposed_price',
            'estimated_delivery',
            'message',
            Submit('submit', 'Зробити ставку', css_class='btn btn-success w-100 mt-3')
        )


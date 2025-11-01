from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import Route, Bid, Tracking, Message, Rating


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


class TrackingUpdateForm(forms.ModelForm):
    class Meta:
        model = Tracking
        fields = ['progress_percent', 'current_location', 'current_lat', 'current_lng']
        widgets = {
            'progress_percent': forms.NumberInput(attrs={
                'class': 'form-control',
                'type': 'range',
                'min': '0',
                'max': '100',
                'step': '1',
                'id': 'progress-slider'
            }),
            'current_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введіть поточну локацію'
            }),
            'current_lat': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': 'Широта'
            }),
            'current_lng': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': 'Довгота'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('progress_percent', css_class='col-12'),
            ),
            Row(
                Column('current_location', css_class='col-12'),
            ),
            Row(
                Column('current_lat', css_class='col-md-6'),
                Column('current_lng', css_class='col-md-6'),
            ),
            Submit('submit', 'Оновити прогрес', css_class='btn btn-primary w-100 mt-3')
        )


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Введіть повідомлення...',
                'style': 'resize: none;'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            'content',
            Submit('submit', 'Відправити', css_class='btn btn-primary mt-2')
        )


class RatingForm(forms.ModelForm):
    """Форма для оцінки перевізника"""
    class Meta:
        model = Rating
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, '★' * i + ' ' + str(i)) for i in range(1, 6)], attrs={
                'class': 'form-select'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Залиште коментар (необов\'язково)...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'rating',
            'comment',
            Submit('rating_submit', 'Зберегти оцінку', css_class='btn btn-primary w-100 mt-3')
        )


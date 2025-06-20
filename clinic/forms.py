from django import forms
from .models import Medicine, MedicineCategory, MedicineRequest, Patient
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = '__all__'
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'shelf_location': forms.Select(choices=Medicine.SHELF_CHOICES),
        }


class MedicineCategoryForm(forms.ModelForm):
    class Meta:
        model = MedicineCategory
        fields = '__all__'


class MedicineRequestForm(forms.ModelForm):
    class Meta:
        model = MedicineRequest
        fields = ['medicine', 'quantity', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show medicines with quantity > 0
        self.fields['medicine'].queryset = Medicine.objects.filter(quantity__gt=0)
        self.fields['medicine'].label_from_instance = lambda \
            obj: f"{obj.name} (Available: {obj.quantity}, Shelf: {obj.shelf_location})"


class MedicineRequestProcessForm(forms.ModelForm):
    class Meta:
        model = MedicineRequest
        fields = ['notes']

class RestockForm(forms.Form):
    medicine = forms.ModelChoiceField(
        queryset=Medicine.objects.all(),
        label="Select Medicine"
    )
    quantity = forms.IntegerField(
        min_value=1,
        label="Quantity to Add"
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label="Restock Notes"
    )
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver


class MedicineCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Medicine(models.Model):
    SHELF_CHOICES = [
        ('Shelf 1', 'Shelf 1'),
        ('Shelf 2', 'Shelf 2'),
        ('Shelf 3', 'Shelf 3'),
        ('Shelf 4', 'Shelf 4'),
    ]
    name = models.CharField(max_length=200)
    category = models.ForeignKey(MedicineCategory, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    expiry_date = models.DateField()
    date_added = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    shelf_location = models.CharField(
        max_length=10,
        choices=SHELF_CHOICES,
        default='Shelf 1'
    )

    def __str__(self):
        return f"{self.name} ({self.category}) - {self.shelf_location}"

    def clean(self):
        if self.quantity < 0:
            raise ValidationError("Quantity cannot be negative")
        if self.reorder_level < 0:
            raise ValidationError("Reorder level cannot be negative")

    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_level

    @property
    def is_near_expiry(self):
        return (self.expiry_date - timezone.now().date()).days <= 30


class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id})"


class MedicineRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='processed_requests')
    processed_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.patient} - {self.medicine} ({self.status})"

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than 0")
        if self.medicine.quantity < self.quantity:
            raise ValidationError("Not enough stock available")

    def save(self, *args, **kwargs):
        if self.status == 'approved' and not self.processed_date:
            self.medicine.quantity -= self.quantity
            self.medicine.save()
            self.processed_date = timezone.now()
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_patient_profile(sender, instance, created, **kwargs):
    if created and not instance.is_staff:
        Patient.objects.create(user=instance, student_id=f"STD-{instance.id}")
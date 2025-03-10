from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)  # Ensures email is unique

    def __str__(self):
        return self.username

User = get_user_model()

class CreditRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    requested_credits = models.PositiveIntegerField()
    approved = models.BooleanField(default=False)
    denied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class DocumentScan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document_name = models.CharField(max_length=255)
    scanned_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField(default='')  # Field to store the text content of the document

class ScanRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=[("Pending", "Pending"), ("Completed", "Completed")])

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credits = models.IntegerField(default=0)
    past_scans = models.ManyToManyField(DocumentScan, blank=True)
    requests = models.ManyToManyField(ScanRequest, blank=True)

    def __str__(self):
        return self.user.username

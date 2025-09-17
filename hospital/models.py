from django.db import models
from django.utils import timezone
from users.models import Profile

SEX_CHOICES = (('M', 'Male'), ('F', 'Female'), ('O', 'Other'))

class Appointment(models.Model):
    patient = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='appointments')  # patient profile
    name = models.CharField(max_length=255)
    age = models.PositiveSmallIntegerField()
    sex = models.CharField(max_length=2, choices=SEX_CHOICES)
    address = models.TextField()
    booked_at = models.DateTimeField(auto_now_add=True)
    doctor = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_appointments')  # assigned doctor (optional)
    status = models.CharField(max_length=50, default='PENDING')  # PENDING, IN_REVIEW, COMPLETED

    def __str__(self):
        return f"Appointment {self.id} - {self.name}"


class Vitals(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='vitals')
    nurse = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='vitals_recorded')
    blood_pressure = models.CharField(max_length=50, blank=True, null=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    blood_sugar = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)


class LabResult(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='lab_results')
    lab_scientist = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='lab_results_posted')
    blood_group = models.CharField(max_length=10, blank=True, null=True)
    test_name = models.CharField(max_length=255, blank=True, null=True)
    result = models.TextField(blank=True, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)


class MedicalReport(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='medical_report')
    doctor = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    medical_condition = models.TextField()
    drug_prescription = models.TextField(blank=True, null=True)
    next_appointment = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


# ---------------- Blog Section ---------------- #

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()  # short intro
    content = models.TextField()      # full article
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='blog_posts')
    featured_image = models.ImageField(upload_to='blog_images/', null=True, blank=True)
    published = models.BooleanField(default=False)
    published_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    class Meta:
        ordering = ['-published_date', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.published and not self.published_date:
            self.published_date = timezone.now()
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

from django.db import models
from django.utils import timezone
from users.models import Profile

SEX_CHOICES = (('M', 'Male'), ('F', 'Female'), ('O', 'Other'))

APPOINTMENT_STATUS = (
    ('PENDING', 'Pending'),
    ('IN_REVIEW', 'In Review'),
    ('AWAITING_RESULTS', 'Awaiting Results'),
    ('COMPLETED', 'Completed'),
    ('CANCELLED', 'Cancelled'),
)

REQUEST_STATUS = (
    ('PENDING', 'Pending'),
    ('IN_PROGRESS', 'In Progress'),
    ('DONE', 'Done'),
    ('CANCELLED', 'Cancelled'),
)

class Appointment(models.Model):
    patient = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='appointments')
    name = models.CharField(max_length=255)
    age = models.PositiveSmallIntegerField()
    sex = models.CharField(max_length=2, choices=SEX_CHOICES)
    address = models.TextField()
    booked_at = models.DateTimeField(auto_now_add=True)
    doctor = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_appointments')
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=APPOINTMENT_STATUS, default='PENDING')

    def __str__(self):
        return f"Appointment {self.id} - {self.name}"


class TestRequest(models.Model):
    """Created by doctor, assigned to a lab scientist (or left unassigned)."""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='test_requests')
    requested_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='test_requests_made')  # doctor
    assigned_to = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='test_requests_assigned')  # lab scientist
    tests = models.TextField(help_text="Comma-separated test list or JSON")  # e.g. "glucose,blood count,urinalysis"
    note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class VitalRequest(models.Model):
    """Created by doctor, assigned to a nurse (or left unassigned)."""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='vital_requests')
    requested_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='vital_requests_made')  # doctor
    assigned_to = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='vital_requests_assigned')  # nurse
    note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Vitals(models.Model):
    vital_request = models.ForeignKey(
        VitalRequest,
        on_delete=models.CASCADE,
        related_name='vitals_entries',
        null=True,  # allow null for existing rows
        blank=True
    )
    nurse = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='vitals_recorded')
    blood_pressure = models.CharField(max_length=50, blank=True, null=True)
    respiration_rate = models.PositiveSmallIntegerField(null=True, blank=True)
    pulse_rate = models.PositiveSmallIntegerField(null=True, blank=True)
    body_temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

class LabResult(models.Model):
    # Link lab result to a TestRequest
    test_request = models.ForeignKey(TestRequest, on_delete=models.CASCADE, related_name='lab_results', null=True, blank=True)
    lab_scientist = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='lab_results_posted')
    test_name = models.CharField(max_length=255)  # e.g. "glucose"
    result = models.TextField(blank=True, null=True)
    units = models.CharField(max_length=50, blank=True, null=True)
    reference_range = models.CharField(max_length=100, blank=True, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

class MedicalReport(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='medical_report')
    doctor = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    medical_condition = models.TextField()
    drug_prescription = models.TextField(blank=True, null=True)
    advice = models.TextField(blank=True, null=True)
    next_appointment = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # mark appointment completed when report is created
        appt = self.appointment
        appt.status = 'COMPLETED'
        appt.save()

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

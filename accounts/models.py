# Import Django's models module for defining database models
from django.db import models
# Import AbstractUser to extend Django's default user model for custom authentication
from django.contrib.auth.models import AbstractUser
# Import uuid for generating unique identifiers for model instances
import uuid
from enum import Enum
from django.utils import timezone

#enum for crop types
class CropType(Enum):
    MAIZE = "MAIZE"
    WHEAT = "WHEAT"
    RICE = "RICE"
    BEANS = "BEANS"
    POTATOES = "POTATOES"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]

# Enum for disease types
class DiseaseType(Enum):
    COMMON_RUST = "common_rust"
    LEAF_BLAST = "leaf_blast"
    GRAY_LEAF_SPOT = "gray_leaf_spot"
    NONE = "none"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]
    
# Enum for urgency levels
class UrgencyLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]
# Custom User model extending AbstractUser for authentication with roles
class User(AbstractUser):
    # Use UUID as primary key for unique, non-sequential IDs (secure and scalable)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Define choices for user roles to distinguish farmers, experts, and admins
    ROLE_CHOICES = [
        ('farmer', 'Farmer'),  # Regular users managing farms
        ('expert', 'Agricultural Expert'),  # Specialists providing advice
        ('admin', 'Admin'),  # System administrators with full control
    ]
    # Store user role to enforce role-based permissions
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    # Use email as unique identifier for login (replaces username)
    email = models.EmailField(unique=True)
    # Optional phone number for contact (can be empty)
    phone_number = models.CharField(max_length=15, blank=True)
    # Flag for admin approval to control access (e.g., experts need verification)
    is_approved = models.BooleanField(default=False)  # Admin approval
    points = models.IntegerField(default=0)  # Points for reward system

    # Set email as the field for authentication (instead of username)
    USERNAME_FIELD = 'email'
    # Require username during user creation (for compatibility)
    REQUIRED_FIELDS = ['username']

    # String representation for easier debugging and admin interface
    def __str__(self):
        return self.email

# # Model to store crop types (e.g., maize, wheat) for farmer profiles
# class CropType(models.Model):
#     # UUID primary key for unique identification
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     # Unique name of the crop type (e.g., "Maize")
#     name = models.CharField(max_length=100, unique=True)

#     # String representation for admin interface and debugging
#     def __str__(self):
#         return self.name

# Model for farmer-specific profile details, linked to User
class FarmerProfile(models.Model):
    # UUID primary key for unique identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # One-to-one link to User model (one profile per farmer)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='farmer_profile')
    # Location of the farm (e.g., "Nairobi")
    farm_location = models.CharField(max_length=200)
    # Size of the farm in acres (required for contextual advice)
    farm_size = models.FloatField()  # Acres
    # Many-to-many relationship with CropType (farmers grow multiple crops)
    crop_types = models.CharField(max_length=200, blank=True, default="")
    # Optional soil type for farm analysis (e.g., "Loamy")
    soil_type = models.CharField(max_length=100, blank=True)
    # Optional irrigation method (e.g., "Drip")
    irrigation_method = models.CharField(max_length=100, blank=True)
    # Optional disease history for tracking farm health
    disease_history = models.TextField(blank=True)
    # Optional GPS coordinates for precise farm location
    farm_latitude = models.FloatField(blank=True, null=True)
    farm_longitude = models.FloatField(blank=True, null=True)
    # Years of farming experience (defaults to 0)
    experience_years = models.IntegerField(default=0)
    # Preferred language for communication (e.g., "English")
    preferred_language = models.CharField(max_length=50, blank=True)
    # Optional list of farm equipment (e.g., "Tractor, Sprayer")
    farm_equipment = models.TextField(blank=True)

    # String representation for admin interface
    def __str__(self):
        return f"{self.user.email}'s Farm"

# Model for expert-specific profile details, linked to User
class ExpertProfile(models.Model):
    # UUID primary key for unique identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # One-to-one link to User model (one profile per expert)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='expert_profile')
    # Areas of expertise (e.g., "Crop Disease, Soil Fertility")
    areas_of_expertise = models.TextField()
    # Optional certifications to build trust (e.g., "PhD in Agronomy")
    certifications = models.TextField(blank=True)
    # Optional biography for expert introduction
    bio = models.TextField(blank=True)
    # Years of professional experience (defaults to 0)
    experience_years = models.IntegerField(default=0)
    # Optional institution affiliation (e.g., "Nairobi University")
    institution = models.CharField(max_length=200, blank=True)
    # Optional languages spoken (e.g., "English, Swahili")
    languages_spoken = models.CharField(max_length=200, blank=True)
    # Optional social media or professional links
    social_links = models.TextField(blank=True)
    validated_responses_count = models.IntegerField(default=0)  # Tracks approved responses

    # String representation for admin interface
    def __str__(self):
        return f"{self.user.email}'s Expertise"

# Model for expert availability slots for consultations
class AvailabilitySlot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expert = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availability_slots')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_booked = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)  # New field for slot status

    def is_expired(self):
        return timezone.now() > self.end_time

    def save(self, *args, **kwargs):
        # Automatically deactivate expired slots
        if self.is_expired():
            self.is_active = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.expert.email}: {self.start_time} - {self.end_time}"

# Model for booking consultations between farmers and experts
class ConsultationBooking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consultations')
    slot = models.OneToOneField(AvailabilitySlot, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # New field
    selected_date = models.DateTimeField(null=True, blank=True)  # Expert-selected date
    created_at = models.DateTimeField(auto_now_add=True)
    notification_sent = models.BooleanField(default=False)  # Track notification status

    def __str__(self):
        return f"{self.farmer.email} with {self.slot.expert.email} ({self.status})"

# Model for community posts by farmers (tips, questions)
# Community post with tags and multimedia
class CommunityPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    disease_type = models.CharField(max_length=50, choices=DiseaseType.choices(), default='none')
    crop_type = models.CharField(max_length=50, choices=CropType.choices(), default='MAIZE')
    urgency_level = models.CharField(max_length=20, choices=UrgencyLevel.choices(), default='low')
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)

    def __str__(self):
        return self.title
# Community response for farmer answers
class CommunityResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='responses')
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_responses')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    expert_comment = models.TextField(blank=True)  # Expert's professional comment
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_responses')

    def __str__(self):
        return f"Response by {self.farmer.email} on {self.post.title}"

# Point transaction for reward system
class PointTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='point_transactions')
    points = models.IntegerField()
    reason = models.CharField(max_length=200)  # e.g., "Posted question", "Approved response"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.points} points for {self.user.email}: {self.reason}"
# Model for farmer feedback on the system
class Feedback(models.Model):
    # UUID primary key for unique identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Link to farmer (User) providing feedback
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback')
    # Feedback content (e.g., suggestions, issues)
    content = models.TextField()
    # Timestamp when feedback was submitted
    created_at = models.DateTimeField(auto_now_add=True)

    # String representation for admin interface
    def __str__(self):
        return f"Feedback from {self.farmer.email}"

# Model for system metrics (e.g., uptime, user activity)
class SystemMetric(models.Model):
    # UUID primary key for unique identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Name of the metric (e.g., "API Uptime")
    metric_name = models.CharField(max_length=100)
    # Value of the metric (e.g., 99.9 for uptime percentage)
    value = models.FloatField()
    # Timestamp when metric was recorded
    recorded_at = models.DateTimeField(auto_now_add=True)

    # String representation for admin interface
    def __str__(self):
        return f"{self.metric_name}: {self.value}"
    
class PasswordResetToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=1)  # 1-hour expiry
        super().save(*args, **kwargs)

    def is_valid(self):
        return timezone.now() <= self.expires_at

    def __str__(self):
        return f"Reset token for {self.user.email}"


class RustAlert(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rust_alerts')
    detection_count = models.IntegerField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert for {self.farmer.email}: {self.detection_count} detections"
    

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.email}: {self.message[:50]}"
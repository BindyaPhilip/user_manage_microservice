# Import Django REST Framework's serializers module to convert models to JSON and validate API input
from rest_framework import serializers
# Import models from the current app to define their serialization behavior
from .models import User, FarmerProfile, ExpertProfile, CropType, AvailabilitySlot, ConsultationBooking, CommunityPost, Feedback, SystemMetric

# Serializer for CropType model to handle crop type data (e.g., "Maize")
class CropTypeSerializer(serializers.ModelSerializer):
    class Meta:
        # Specify the model to serialize
        model = CropType
        # Fields to include in the JSON output/input validation
        fields = ['id', 'name']

# Serializer for User model to handle user data (e.g., email, role)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        # Specify the model to serialize
        model = User
        # Fields to include, covering key user attributes
        fields = ['id', 'email', 'username', 'role', 'phone_number', 'is_approved']

# Serializer for FarmerProfile model to handle farmer-specific data
class FarmerProfileSerializer(serializers.ModelSerializer):
    # Nested serializer for crop_types (many-to-many relationship), allowing full crop type details
    crop_types = CropTypeSerializer(many=True)
    # Nested serializer for user, read-only to prevent modifying user data via profile updates
    user = UserSerializer(read_only=True)

    class Meta:
        # Specify the model to serialize
        model = FarmerProfile
        # Fields to include, covering all farmer profile attributes
        fields = ['id', 'user', 'farm_location', 'farm_size', 'crop_types', 'soil_type', 'irrigation_method', 'disease_history', 'farm_latitude', 'farm_longitude', 'experience_years', 'preferred_language', 'farm_equipment']

    # Custom update method to handle updating crop_types (many-to-many relationship)
    def update(self, instance, validated_data):
        # Remove crop_types data from validated_data to process separately
        crop_types_data = validated_data.pop('crop_types', [])
        # Call parent update method to handle standard fields
        instance = super().update(instance, validated_data)
        # If crop_types data is provided, update the many-to-many relationship
        if crop_types_data:
            # Extract IDs from crop_types_data (assuming IDs are provided)
            crop_type_ids = [ct['id'] for ct in crop_types_data if 'id' in ct]
            # Update crop_types by setting only the specified IDs
            instance.crop_types.set(CropType.objects.filter(id__in=crop_type_ids))
        return instance

# Serializer for ExpertProfile model to handle expert-specific data
class ExpertProfileSerializer(serializers.ModelSerializer):
    # Nested serializer for user, read-only to prevent modifying user data
    user = UserSerializer(read_only=True)

    class Meta:
        # Specify the model to serialize
        model = ExpertProfile
        # Fields to include, covering all expert profile attributes
        fields = ['id', 'user', 'areas_of_expertise', 'certifications', 'bio', 'experience_years', 'institution', 'languages_spoken', 'social_links']

# Serializer for AvailabilitySlot model to handle expert consultation slots
class AvailabilitySlotSerializer(serializers.ModelSerializer):
    # Nested serializer for expert, read-only to show expert details without modification
    expert = UserSerializer(read_only=True)

    class Meta:
        # Specify the model to serialize
        model = AvailabilitySlot
        # Fields to include, covering slot details
        fields = ['id', 'expert', 'start_time', 'end_time', 'is_booked']

# Serializer for ConsultationBooking model to handle farmer-expert bookings
class ConsultationBookingSerializer(serializers.ModelSerializer):
    # Nested serializer for farmer, read-only to show farmer details
    farmer = UserSerializer(read_only=True)
    # Nested serializer for slot, read-only to show slot details
    slot = AvailabilitySlotSerializer(read_only=True)

    class Meta:
        # Specify the model to serialize
        model = ConsultationBooking
        # Fields to include, covering booking details
        fields = ['id', 'farmer', 'slot', 'created_at']

# Serializer for CommunityPost model to handle farmer posts
class CommunityPostSerializer(serializers.ModelSerializer):
    # Nested serializer for farmer, read-only to show post author
    farmer = UserSerializer(read_only=True)

    class Meta:
        # Specify the model to serialize
        model = CommunityPost
        # Fields to include, covering post details
        fields = ['id', 'farmer', 'title', 'content', 'created_at', 'is_approved', 'is_flagged']

# Serializer for Feedback model to handle farmer feedback
class FeedbackSerializer(serializers.ModelSerializer):
    # Nested serializer for farmer, read-only to show feedback author
    farmer = UserSerializer(read_only=True)

    class Meta:
        # Specify the model to serialize
        model = Feedback
        # Fields to include, covering feedback details
        fields = ['id', 'farmer', 'content', 'created_at']

# Serializer for SystemMetric model to handle system performance metrics
class SystemMetricSerializer(serializers.ModelSerializer):
    class Meta:
        # Specify the model to serialize
        model = SystemMetric
        # Fields to include, covering metric details
        fields = ['id', 'metric_name', 'value', 'recorded_at']
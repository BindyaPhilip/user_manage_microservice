# Import Django REST Framework's serializers module to convert models to JSON and validate API input
from django.utils import timezone
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
# Import models from the current app to define their serialization behavior
from .models import User, FarmerProfile, ExpertProfile, CropType, AvailabilitySlot, ConsultationBooking, CommunityPost, Feedback, SystemMetric,PasswordResetToken,CommunityResponse,PointTransaction
from django.contrib.auth.hashers import make_password
# Serializer for CropType model to handle crop type data (e.g., "Maize")
# class CropTypeSerializer(serializers.ModelSerializer):
#     class Meta:
#         # Specify the model to serialize
#         model = CropType
#         # Fields to include in the JSON output/input validation
#         fields = ['id', 'name']

# Serializer for User model to handle user data (e.g., email, role)
# User serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password', 'role', 'phone_number', 'is_approved', 'points']
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True},
            'role': {'read_only': True},
            'is_approved': {'read_only': True},
            'points': {'read_only': True},
        }

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        validated_data['is_active'] = True
        return super().create(validated_data)

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.username = validated_data.get('username', instance.username)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.save()
        return instance

# Serializer for FarmerProfile model to handle farmer-specific data
class FarmerProfileSerializer(serializers.ModelSerializer):
    # Nested serializer for crop_types (many-to-many relationship), allowing full crop type details
    crop_types = serializers.ListField(
        child=serializers.ChoiceField(choices=CropType.choices()),
        allow_empty=True,
        required=False
    )
    # Nested serializer for user, read-only to prevent modifying user data via profile updates
    user = UserSerializer(read_only=True)

    class Meta:
        # Specify the model to serialize
        model = FarmerProfile
        # Fields to include, covering all farmer profile attributes
        fields = ['id', 'user', 'farm_location', 'farm_size', 'crop_types', 'soil_type', 'irrigation_method', 'disease_history', 'farm_latitude', 'farm_longitude', 'experience_years', 'preferred_language', 'farm_equipment']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['crop_types'] = instance.crop_types.split(',') if instance.crop_types else []
        return ret

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        crop_types = data.get('crop_types', [])
        if crop_types:
            valid_choices = [choice[0] for choice in CropType.choices()]
            for ct in crop_types:
                if ct not in valid_choices:
                    raise serializers.ValidationError(f"Invalid crop type: {ct}")
            ret['crop_types'] = ','.join(crop_types)
        else:
            ret['crop_types'] = ''
        return ret
    
class RegisterFarmerSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    phone_number = serializers.CharField(max_length=15, required=False, allow_blank=True)
    farm_location = serializers.CharField(max_length=200)
    farm_size = serializers.FloatField()
    crop_types = serializers.ListField(
        child=serializers.ChoiceField(choices=CropType.choices()),
        allow_empty=True,
        required=False
    )

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        crop_types = validated_data.pop('crop_types', [])
        user_data = {
            'email': validated_data['email'],
            'username': validated_data['username'],
            'phone_number': validated_data.get('phone_number', ''),
            'role': 'farmer',
            'is_active': True  # Ensure user is active
        }
        user = User.objects.create_user(**user_data, password=validated_data['password'])
        profile_data = {
            'user': user,
            'farm_location': validated_data['farm_location'],
            'farm_size': validated_data['farm_size'],
            'crop_types': ','.join(crop_types) if crop_types else ''
        }
        profile = FarmerProfile.objects.create(**profile_data)
        return {'user': UserSerializer(user).data, 'profile': FarmerProfileSerializer(profile).data}


# # Serializer for ExpertProfile model to handle expert-specific data
# class ExpertProfileSerializer(serializers.ModelSerializer):
#     # Nested serializer for user, read-only to prevent modifying user data
#     user = UserSerializer(read_only=False, partial = True)

#     class Meta:
#         # Specify the model to serialize
#         model = ExpertProfile
#         # Fields to include, covering all expert profile attributes
#         fields = ['id', 'user', 'areas_of_expertise', 'certifications', 'bio', 'experience_years', 'institution', 'languages_spoken', 'social_links']
#     def update(self, instance, validated_data):
#         # Handle nested user data
#         user_data = validated_data.pop('user', None)
#         if user_data:
#             user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
#             if user_serializer.is_valid():
#                 user_serializer.save()
#             else:
#                 raise serializers.ValidationError(user_serializer.errors)

#         # Update ExpertProfile fields
#         return super().update(instance, validated_data)

# Expert profile serializer
class ExpertProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=False, partial=True, required=False)

    class Meta:
        model = ExpertProfile
        fields = ['id', 'user', 'areas_of_expertise', 'certifications', 'bio', 'experience_years', 'institution', 'languages_spoken', 'social_links', 'validated_responses_count']
        extra_kwargs = {
            'validated_responses_count': {'read_only': True}
        }

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
            if user_serializer.is_valid():
                user_serializer.save()
            else:
                raise serializers.ValidationError(user_serializer.errors)
        return super().update(instance, validated_data)

class RegisterExpertSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    phone_number = serializers.CharField(max_length=15, required=False, allow_blank=True)
    areas_of_expertise = serializers.CharField()
    certifications = serializers.CharField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    experience_years = serializers.IntegerField(default=0)
    institution = serializers.CharField(required=False, allow_blank=True)
    languages_spoken = serializers.CharField(required=False, allow_blank=True)
    social_links = serializers.CharField(required=False, allow_blank=True)


    def create(self, validated_data):
        user_data = {
            'email': validated_data['email'],
            'username': validated_data['username'],
            'phone_number': validated_data.get('phone_number', ''),
            'role': 'expert',
            'is_active': True,
            'is_approved': True  # Auto-approve for simplicity; adjust if needed
        }
        user = User.objects.create_user(**user_data, password=validated_data['password'])
        profile_data = {
            'user': user,
            'areas_of_expertise': validated_data['areas_of_expertise'],
            'certifications': validated_data.get('certifications', ''),
            'bio': validated_data.get('bio', ''),
            'experience_years': validated_data.get('experience_years', 0),
            'institution': validated_data.get('institution', ''),
            'languages_spoken': validated_data.get('languages_spoken', ''),
            'social_links': validated_data.get('social_links', ''),
        }
        profile = ExpertProfile.objects.create(**profile_data)
        return {'user': UserSerializer(user).data, 'profile': ExpertProfileSerializer(profile).data}


# Community response serializer
class CommunityResponseSerializer(serializers.ModelSerializer):
    farmer = UserSerializer(read_only=True)
    approved_by = UserSerializer(read_only=True)
    post = serializers.UUIDField(write_only=True)

    class Meta:
        model = CommunityResponse
        fields = ['id', 'post', 'farmer', 'content', 'created_at', 'is_approved', 'expert_comment', 'approved_by']
        extra_kwargs = {
            'is_approved': {'read_only': True},
            'expert_comment': {'read_only': True},
            'approved_by': {'read_only': True}
        }

    def create(self, validated_data):
        validated_data['farmer'] = self.context['request'].user
        validated_data['post'] = CommunityPost.objects.get(id=validated_data['post'])
        response = super().create(validated_data)
        # Award points for posting a response
        user = response.farmer
        user.points += 3
        user.save()
        PointTransaction.objects.create(user=user, points=3, reason="Posted community response")
        return response
# Serializer for AvailabilitySlot model to handle expert consultation slots
class AvailabilitySlotSerializer(serializers.ModelSerializer):
    # Override the expert field to use the related ExpertProfile
    expert = serializers.SerializerMethodField()

    class Meta:
        model = AvailabilitySlot
        fields = ['id', 'expert', 'start_time', 'end_time', 'is_booked', 'is_active']
        extra_kwargs = {
            'is_booked': {'read_only': True},
            'is_active': {'read_only': True},
        }

    def get_expert(self, obj):
        # Access the ExpertProfile related to the User
        try:
            expert_profile = obj.expert.expert_profile
            return ExpertProfileSerializer(expert_profile).data
        except ExpertProfile.DoesNotExist:
            # Handle cases where ExpertProfile doesn't exist
            return None  # Or return a default dict, e.g., {'email': obj.expert.email}

    def validate(self, data):
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        if start_time >= end_time:
            raise serializers.ValidationError({"end_time": "End time must be after start time"})
        if start_time < timezone.now():
            raise serializers.ValidationError({"start_time": "Start time cannot be in the past"})
        # Check for overlapping slots
        existing_slots = AvailabilitySlot.objects.filter(
            expert=self.context['request'].user,
            is_active=True,
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        if existing_slots.exists():
            raise serializers.ValidationError({"non_field_errors": "Slot overlaps with an existing active slot"})
        return data

    def create(self, validated_data):
        validated_data['expert'] = self.context['request'].user
        return AvailabilitySlot.objects.create(**validated_data)

# Serializer for ConsultationBooking model to handle farmer-expert bookings
class ConsultationBookingSerializer(serializers.ModelSerializer):
    farmer = UserSerializer(read_only=True)
    slot = AvailabilitySlotSerializer(read_only=True)
    selected_date = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = ConsultationBooking
        fields = ['id', 'farmer', 'slot', 'status', 'selected_date', 'created_at', 'notification_sent']
        extra_kwargs = {
            'status': {'read_only': True},
            'notification_sent': {'read_only': True},
        }

    def validate(self, data):
        slot_id = data.get('slot_id')
        try:
            slot = AvailabilitySlot.objects.get(id=slot_id, is_booked=False, is_active=True)
            if slot.is_expired():
                raise serializers.ValidationError({"slot_id": "This slot has expired"})
        except AvailabilitySlot.DoesNotExist:
            raise serializers.ValidationError({"slot_id": "Slot unavailable or invalid"})
        return data


# Community post serializer
class CommunityPostSerializer(serializers.ModelSerializer):
    farmer = UserSerializer(read_only=True)
    farmer_comments = serializers.SerializerMethodField()
    expert_comments = serializers.SerializerMethodField()

    class Meta:
        model = CommunityPost
        fields = [
            'id', 'farmer', 'title', 'content', 'disease_type', 'crop_type',
            'urgency_level', 'created_at', 'is_approved', 'is_flagged',
            'farmer_comments', 'expert_comments'
        ]
        extra_kwargs = {
            'is_approved': {'read_only': True},
            'is_flagged': {'read_only': True}
        }

    def get_farmer_comments(self, obj):
        # Return approved comments by farmers
        farmer_responses = obj.responses.filter(is_approved=True, farmer__role='farmer')
        return CommunityResponseSerializer(farmer_responses, many=True).data

    def get_expert_comments(self, obj):
        # Return approved comments by experts (based on expert_comment field)
        expert_responses = obj.responses.filter(is_approved=True, expert_comment__isnull=False)
        return [
            {
                'id': response.id,
                'expert': UserSerializer(response.approved_by).data,
                'content': response.expert_comment,
                'created_at': response.created_at,
            }
            for response in expert_responses
        ]

    def create(self, validated_data):
        validated_data['farmer'] = self.context['request'].user
        post = super().create(validated_data)
        # Award points for posting a question
        user = post.farmer
        user.points += 5
        user.save()
        PointTransaction.objects.create(user=user, points=5, reason="Posted community question")
        return post


class FarmerPostCountSerializer(serializers.Serializer):
    farmer_id = serializers.UUIDField()
    post_count = serializers.IntegerField()
# Point transaction serializer
class PointTransactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = PointTransaction
        fields = ['id', 'user', 'points', 'reason', 'created_at']
        extra_kwargs = {
            'points': {'read_only': True},
            'reason': {'read_only': True},
            'created_at': {'read_only': True}
        }
# Serializer for CommunityPost model to handle farmer posts
# class CommunityPostSerializer(serializers.ModelSerializer):
#     # Nested serializer for farmer, read-only to show post author
#     farmer = UserSerializer(read_only=True)

#     class Meta:
#         # Specify the model to serialize
#         model = CommunityPost
#         # Fields to include, covering post details
#         fields = ['id', 'farmer', 'title', 'content', 'created_at', 'is_approved', 'is_flagged']

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

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New passwords do not match"})
        user = self.context['request'].user
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({"old_password": "Incorrect old password"})
        return data
    
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email")
        return value
    

class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        try:
            reset_token = PasswordResetToken.objects.get(token=data['token'])
            if not reset_token.is_valid():
                raise serializers.ValidationError({"token": "Token has expired"})
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError({"token": "Invalid token"})
        return data
    

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims to the token (optional)
        token['email'] = user.email
        token['role'] = user.role
        return token

    def validate(self, attrs):
        # Validate credentials and get token data
        data = super().validate(attrs)

        # Get the authenticated user
        user = self.user

        # Prepare user data
        user_data = {
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'role': user.role,
            'phone_number': user.phone_number or None,
        }

        # Include profile data based on user role
        if user.role == 'farmer':
            try:
                profile = user.farmer_profile
                user_data['profile'] = FarmerProfileSerializer(profile).data
            except FarmerProfile.DoesNotExist:
                user_data['profile'] = None
        elif user.role == 'expert':
            try:
                profile = user.expert_profile
                user_data['profile'] = ExpertProfileSerializer(profile).data
            except ExpertProfile.DoesNotExist:
                user_data['profile'] = None
        else:  # admin or other roles
            user_data['profile'] = None

        # Add user data to the response
        data['user'] = user_data

        return data
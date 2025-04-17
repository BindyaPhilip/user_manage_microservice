# Import APIView to create class-based views for handling HTTP requests
from rest_framework.views import APIView
# Import Response to return JSON responses to clients
from rest_framework.response import Response
# Import status to use HTTP status codes (e.g., 201 Created, 400 Bad Request)
from rest_framework import status
# Import PageNumberPagination for paginating large query results
from rest_framework.pagination import PageNumberPagination
# Import models to interact with database objects
from .models import User, FarmerProfile, ExpertProfile, CropType, AvailabilitySlot, ConsultationBooking, CommunityPost, Feedback, SystemMetric
# Import serializers to validate input and serialize output to JSON
from .serializers import UserSerializer, FarmerProfileSerializer, ExpertProfileSerializer, CropTypeSerializer, AvailabilitySlotSerializer, ConsultationBookingSerializer, CommunityPostSerializer, FeedbackSerializer, SystemMetricSerializer
# Import custom permissions to restrict access based on user roles
from .permissions import IsFarmer, IsExpert, IsAdmin, IsFarmerOrAdmin, IsExpertOrAdmin
# Import AllowAny to allow unauthenticated access (e.g., for registration)
from rest_framework.permissions import AllowAny
# Import requests to make HTTP calls to other microservices
import requests
# Import send_mail to send email alerts
from django.core.mail import send_mail
# Import shared_task to define Celery tasks for asynchronous operations
from celery import shared_task
# Import timezone for timezone-aware date/time handling
from django.utils import timezone
# Import timedelta for time-based calculations (e.g., recent feedback)
from datetime import timedelta

# Celery task to send asynchronous email alerts to farmers about detected diseases
@shared_task
def send_alert_email(farmer_email, disease):
    # Define email subject with the detected disease (e.g., "Disease Alert: Common Rust Detected")
    subject = f"Disease Alert: {disease} Detected"
    # Define email message with advice to consult experts or resources
    message = f"Multiple detections of {disease} have been recorded on your farm. Please consult an expert or refer to educational resources."
    # Send email using Django's send_mail function
    send_mail(subject, message, 'from@example.com', [farmer_email])

# API view to handle farmer registration
class RegisterFarmerView(APIView):
    # Allow anyone to access (no authentication required for registration)
    permission_classes = [AllowAny]

    # Handle POST requests to create a new farmer user and profile
    def post(self, request):
        # Copy request data to modify (e.g., add role)
        data = request.data.copy()
        # Set role to 'farmer' for this user
        data['role'] = 'farmer'
        # Initialize UserSerializer to validate user data (email, password, etc.)
        user_serializer = UserSerializer(data=data)
        # Check if user data is valid
        if user_serializer.is_valid():
            # Save the user to the database
            user = user_serializer.save()
            # Prepare profile data with defaults for optional fields
            profile_data = {
                'farm_location': data.get('farm_location', ''),
                'farm_size': data.get('farm_size', 0),
                'soil_type': data.get('soil_type', ''),
                'irrigation_method': data.get('irrigation_method', ''),
                'disease_history': data.get('disease_history', ''),
                'farm_latitude': data.get('farm_latitude'),
                'farm_longitude': data.get('farm_longitude'),
                'experience_years': data.get('experience_years', 0),
                'preferred_language': data.get('preferred_language', ''),
                'farm_equipment': data.get('farm_equipment', ''),
                'user': user.id,  # Link profile to the created user
            }
            # Initialize FarmerProfileSerializer to validate profile data
            profile_serializer = FarmerProfileSerializer(data=profile_data)
            # Check if profile data is valid
            if profile_serializer.is_valid():
                # Save the farmer profile
                profile = profile_serializer.save()
                # Get crop type IDs from request (many-to-many relationship)
                crop_types = data.get('crop_types', [])
                # Link crop types to the profile
                profile.crop_types.set(CropType.objects.filter(id__in=crop_types))
                # Return success response with user and profile data
                return Response({'user': user_serializer.data, 'profile': profile_serializer.data}, status=status.HTTP_201_CREATED)
            # If profile fails, delete user to avoid orphaned records
            user.delete()
            # Return profile validation errors
            return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # Return user validation errors
        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# API view to handle expert registration
class RegisterExpertView(APIView):
    # Allow anyone to access (no authentication required for registration)
    permission_classes = [AllowAny]

    # Handle POST requests to create a new expert user and profile
    def post(self, request):
        # Copy request data to modify
        data = request.data.copy()
        # Set role to 'expert' for this user
        data['role'] = 'expert'
        # Initialize UserSerializer to validate user data
        user_serializer = UserSerializer(data=data)
        # Check if user data is valid
        if user_serializer.is_valid():
            # Save the user
            user = user_serializer.save()
            # Prepare profile data with defaults
            profile_data = {
                'areas_of_expertise': data.get('areas_of_expertise', ''),
                'certifications': data.get('certifications', ''),
                'bio': data.get('bio', ''),
                'experience_years': data.get('experience_years', 0),
                'institution': data.get('institution', ''),
                'languages_spoken': data.get('languages_spoken', ''),
                'social_links': data.get('social_links', ''),
                'user': user.id,  # Link profile to the created user
            }
            # Initialize ExpertProfileSerializer to validate profile data
            profile_serializer = ExpertProfileSerializer(data=profile_data)
            # Check if profile data is valid
            if profile_serializer.is_valid():
                # Save the expert profile
                profile = profile_serializer.save()
                # Return success response
                return Response({'user': user_serializer.data, 'profile': profile_serializer.data}, status=status.HTTP_201_CREATED)
            # If profile fails, delete user
            user.delete()
            # Return profile validation errors
            return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # Return user validation errors
        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# API view for farmers to view or update their profile
class FarmerProfileView(APIView):
    # Restrict access to authenticated farmers only
    permission_classes = [IsFarmer]

    # Handle GET requests to retrieve the farmer's profile
    def get(self, request):
        # Access the farmer's profile via the authenticated user
        profile = request.user.farmer_profile
        # Serialize the profile data
        serializer = FarmerProfileSerializer(profile)
        # Return the serialized data
        return Response(serializer.data)

    # Handle PUT requests to update the farmer's profile
    def put(self, request):
        # Access the farmer's profile
        profile = request.user.farmer_profile
        # Initialize serializer with existing profile and new data (partial updates allowed)
        serializer = FarmerProfileSerializer(profile, data=request.data, partial=True)
        # Check if data is valid
        if serializer.is_valid():
            # Save the updated profile
            serializer.save()
            # Return updated data
            return Response(serializer.data)
        # Return validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# API view for experts to view or update their profile
class ExpertProfileView(APIView):
    # Restrict access to authenticated experts only
    permission_classes = [IsExpert]

    # Handle GET requests to retrieve the expert's profile
    def get(self, request):
        # Access the expert's profile
        profile = request.user.expert_profile
        # Serialize the profile data
        serializer = ExpertProfileSerializer(profile)
        # Return the serialized data
        return Response(serializer.data)

    # Handle PUT requests to update the expert's profile
    def put(self, request):
        # Access the expert's profile
        profile = request.user.expert_profile
        # Initialize serializer with existing profile and new data
        serializer = ExpertProfileSerializer(profile, data=request.data, partial=True)
        # Check if data is valid
        if serializer.is_valid():
            # Save the updated profile
            serializer.save()
            # Return updated data
            return Response(serializer.data)
        # Return validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# API view for farmers to view disease detection history from image_analysis microservice
class DiseaseHistoryView(APIView):
    # Restrict access to authenticated farmers
    permission_classes = [IsFarmer]
    # Use pagination to handle large detection lists
    pagination_class = PageNumberPagination

    # Handle GET requests to fetch rust detection history
    def get(self, request):
        try:
            # Make HTTP GET request to image_analysis microservice
            response = requests.get('http://localhost:8000/api/rust-detection/', headers={'Authorization': f'Bearer {request.auth}'})
            # Raise exception for HTTP errors
            response.raise_for_status()
            # Parse JSON response
            detections = response.json()
            # Paginate the detection data
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(detections, request)
            # Return paginated response
            return paginator.get_paginated_response(page)
        except requests.RequestException as e:
            # Return error if request fails
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# API view for farmers to check crop health alerts based on detection frequency
class CropHealthAlertView(APIView):
    # Restrict access to authenticated farmers
    permission_classes = [IsFarmer]

    # Handle GET requests to check for disease alerts
    def get(self, request):
        try:
            # Fetch detection history from image_analysis microservice
            response = requests.get('http://localhost:8000/api/rust-detection/', headers={'Authorization': f'Bearer {request.auth}'})
            response.raise_for_status()
            detections = response.json()
            # Count occurrences of each disease
            disease_counts = {}
            for detection in detections:
                disease = detection['rust_class']
                disease_counts[disease] = disease_counts.get(disease, 0) + 1
                # Trigger email alert if disease detected 3+ times
                if disease_counts.get(disease, 0) >= 3:
                    send_alert_email.delay(request.user.email, disease)
            # Return status and disease counts
            return Response({'status': 'Checked for alerts', 'counts': disease_counts})
        except requests.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# API view for farmers to view/post community posts, admins to view
class CommunityPostView(APIView):
    # Restrict to farmers or admins
    permission_classes = [IsFarmerOrAdmin]

    # Handle GET requests to list approved posts
    def get(self, request):
        # Filter posts that are approved
        posts = CommunityPost.objects.filter(is_approved=True)
        # Serialize posts (multiple)
        serializer = CommunityPostSerializer(posts, many=True)
        # Return serialized data
        return Response(serializer.data)

    # Handle POST requests to create a new post
    def post(self, request):
        # Only farmers can create posts
        if request.user.role != 'farmer':
            return Response({'error': 'Only farmers can post'}, status=status.HTTP_403_FORBIDDEN)
        # Copy data and link to current user
        data = request.data.copy()
        data['farmer'] = request.user.id
        # Initialize serializer
        serializer = CommunityPostSerializer(data=data)
        # Check if data is valid
        if serializer.is_valid():
            # Save the post
            serializer.save()
            # Return created post data
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # Return validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# API view for experts/admins to moderate community posts
class CommunityPostModerationView(APIView):
    # Restrict to experts or admins
    permission_classes = [IsExpertOrAdmin]

    # Handle GET requests to list unapproved posts
    def get(self, request):
        # Filter unapproved posts
        posts = CommunityPost.objects.filter(is_approved=False)
        # Serialize posts
        serializer = CommunityPostSerializer(posts, many=True)
        # Return serialized data
        return Response(serializer.data)

    # Handle PUT requests to approve/flag/unflag a post
    def put(self, request, post_id):
        try:
            # Get the post by ID
            post = CommunityPost.objects.get(id=post_id)
            # Get action from request (approve, flag, unflag)
            action = request.data.get('action')
            if action == 'approve':
                post.is_approved = True
            elif action == 'flag':
                post.is_flagged = True
            elif action == 'unflag':
                post.is_flagged = False
            else:
                # Return error for invalid action
                return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
            # Save changes
            post.save()
            # Return updated post data
            return Response(CommunityPostSerializer(post).data)
        except CommunityPost.DoesNotExist:
            # Return error if post not found
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

# API view for experts to submit educational content to education microservice
class EducationalContentSubmissionView(APIView):
    # Restrict to experts
    permission_classes = [IsExpert]

    # Handle POST requests to submit content
    def post(self, request):
        # Prepare data for education microservice
        data = {
            'title': request.data.get('title'),
            'url': request.data.get('url'),
            'description': request.data.get('description'),
            'disease': request.data.get('disease'),
            'resource_type': request.data.get('resource_type'),
        }
        try:
            # Make POST request to education microservice
            response = requests.post('http://localhost:8001/api/resources/', json=data, headers={'Authorization': f'Bearer {request.auth}'})
            response.raise_for_status()
            # Return response from education microservice
            return Response(response.json(), status=status.HTTP_201_CREATED)
        except requests.RequestException as e:
            # Return error if request fails
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# API view for experts to manage availability slots
class AvailabilitySlotView(APIView):
    # Restrict to experts
    permission_classes = [IsExpert]

    # Handle GET requests to list available slots
    def get(self, request):
        # Filter unbooked slots for the current expert
        slots = AvailabilitySlot.objects.filter(expert=request.user, is_booked=False)
        # Serialize slots
        serializer = AvailabilitySlotSerializer(slots, many=True)
        # Return serialized data
        return Response(serializer.data)

    # Handle POST requests to create a new slot
    def post(self, request):
        # Copy data and link to current expert
        data = request.data.copy()
        data['expert'] = request.user.id
        # Initialize serializer
        serializer = AvailabilitySlotSerializer(data=data)
        # Check if data is valid
        if serializer.is_valid():
            # Save the slot
            serializer.save()
            # Return created slot data
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # Return validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# API view for farmers to manage consultation bookings
class ConsultationBookingView(APIView):
    # Restrict to farmers
    permission_classes = [IsFarmer]

    # Handle GET requests to list bookings
    def get(self, request):
        # Filter bookings for the current farmer
        bookings = ConsultationBooking.objects.filter(farmer=request.user)
        # Serialize bookings
        serializer = ConsultationBookingSerializer(bookings, many=True)
        # Return serialized data
        return Response(serializer.data)

    # Handle POST requests to create a booking
    def post(self, request):
        # Get slot ID from request
        slot_id = request.data.get('slot_id')
        try:
            # Get unbooked slot by ID
            slot = AvailabilitySlot.objects.get(id=slot_id, is_booked=False)
            # Create booking for the current farmer
            booking = ConsultationBooking(farmer=request.user, slot=slot)
            # Mark slot as booked
            slot.is_booked = True
            slot.save()
            # Save booking
            booking.save()
            # Serialize and return booking data
            serializer = ConsultationBookingSerializer(booking)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except AvailabilitySlot.DoesNotExist:
            # Return error if slot is unavailable
            return Response({'error': 'Slot unavailable'}, status=status.HTTP_400_BAD_REQUEST)

# API view for admins to manage users
class UserManagementView(APIView):
    # Restrict to admins
    permission_classes = [IsAdmin]

    # Handle GET requests to list all users
    def get(self, request):
        # Get all users
        users = User.objects.all()
        # Serialize users
        serializer = UserSerializer(users, many=True)
        # Return serialized data
        return Response(serializer.data)

    # Handle PUT requests to update a user (approve, block, or edit)
    def put(self, request, user_id):
        try:
            # Get user by ID
            user = User.objects.get(id=user_id)
            # Get action from request
            action = request.data.get('action')
            if action == 'approve':
                # Approve the user
                user.is_approved = True
            elif action == 'block':
                # Block the user (deactivate)
                user.is_approved = False
                user.is_active = False
            else:
                # Update user data (e.g., role, email)
                serializer = UserSerializer(user, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            # Save changes
            user.save()
            # Return updated user data
            return Response(UserSerializer(user).data)
        except User.DoesNotExist:
            # Return error if user not found
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

# API view for admins to view system metrics
class SystemHealthView(APIView):
    # Restrict to admins
    permission_classes = [IsAdmin]

    # Handle GET requests to list all metrics
    def get(self, request):
        # Get all system metrics
        metrics = SystemMetric.objects.all()
        # Serialize metrics
        serializer = SystemMetricSerializer(metrics, many=True)
        # Return serialized data
        return Response(serializer.data)

# API view for admins to trigger model retraining
class ModelRetrainingView(APIView):
    # Restrict to admins
    permission_classes = [IsAdmin]

    # Handle POST requests to trigger retraining
    def post(self, request):
        try:
            # Make POST request to image_analysis microservice to trigger retraining
            response = requests.post('http://localhost:8000/api/upload-training-images/', data=request.data, headers={'Authorization': f'Bearer {request.auth}'})
            response.raise_for_status()
            # Return success response
            return Response({'status': 'Retraining triggered'}, status=status.HTTP_200_OK)
        except requests.RequestException as e:
            # Return error if request fails
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# API view for admins to analyze feedback
class FeedbackAnalysisView(APIView):
    # Restrict to admins
    permission_classes = [IsAdmin]

    # Handle GET requests to summarize feedback
    def get(self, request):
        # Get all feedback
        feedback = Feedback.objects.all()
        # Count total feedback
        total = feedback.count()
        # Count feedback from last 30 days
        recent = feedback.filter(created_at__gte=timezone.now() - timedelta(days=30)).count()
        # Return summary
        return Response({'total_feedback': total, 'recent_feedback': recent})

# API view for admins to approve community posts
class ContentApprovalView(APIView):
    # Restrict to admins
    permission_classes = [IsAdmin]

    # Handle GET requests to list unapproved posts
    def get(self, request):
        # Filter unapproved posts
        posts = CommunityPost.objects.filter(is_approved=False)
        # Serialize posts
        serializer = CommunityPostSerializer(posts, many=True)
        # Return serialized data
        return Response(serializer.data)

    # Handle PUT requests to approve a post
    def put(self, request, post_id):
        try:
            # Get post by ID
            post = CommunityPost.objects.get(id=post_id)
            # Update approval status
            post.is_approved = request.data.get('is_approved', False)
            # Save changes
            post.save()
            # Return updated post data
            return Response(CommunityPostSerializer(post).data)
        except CommunityPost.DoesNotExist:
            # Return error if post not found
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
# Import APIView to create class-based views for handling HTTP requests
import uuid
from rest_framework.views import APIView
# Import Response to return JSON responses to clients
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework.response import Response
# Import status to use HTTP status codes (e.g., 201 Created, 400 Bad Request)
from rest_framework import status
# Import PageNumberPagination for paginating large query results
from rest_framework.pagination import PageNumberPagination
import logging
from dateutil.parser import parse as parse_datetime  # Import dateutil.parser
from django.utils.dateparse import parse_datetime as django_parse_datetime
from user_management import settings
# Import models to interact with database objects
from .models import Notification, User, FarmerProfile, ExpertProfile, CropType, AvailabilitySlot, ConsultationBooking, CommunityPost, Feedback, SystemMetric, PasswordResetToken, RustAlert, PointTransaction, CommunityResponse, DiseaseType, UrgencyLevel
# Import serializers to validate input and serialize output to JSON
from .serializers import ChangePasswordSerializer, UserSerializer, FarmerProfileSerializer, ExpertProfileSerializer, AvailabilitySlotSerializer, ConsultationBookingSerializer, CommunityPostSerializer, FeedbackSerializer, SystemMetricSerializer, RegisterFarmerSerializer, ForgotPasswordSerializer, ResetPasswordSerializer, CommunityResponseSerializer, PointTransactionSerializer, RegisterExpertSerializer,FarmerPostCountSerializer

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
# Import swagger_auto_schema for Swagger documentation
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from datetime import timezone as dt_timezone

logger = logging.getLogger(__name__)

# Celery task to send asynchronous email alerts to farmers about detected diseases
@shared_task
def send_alert_email(farmer_email, disease):
    """
    Celery task to send email alerts about detected diseases.
    
    Args:
        farmer_email (str): Email address of the farmer.
        disease (str): Name of the detected disease.
    """
    subject = f"Disease Alert: {disease} Detected"
    message = f"Multiple detections of {disease} have been recorded on your farm. Please consult an expert or refer to educational resources."
    send_mail(subject, message, 'from@example.com', [farmer_email])

class CropTypeView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description=(
            "Retrieve a list of available crop types for use in other endpoints (e.g., farmer registration, community posts).\n\n"
            "**Permissions**: Public (no authentication required).\n"
            "**Returns**: A list of crop types with their values and labels (e.g., `MAIZE`, `WHEAT`)."
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'value': openapi.Schema(type=openapi.TYPE_STRING, description='Crop type value'),
                        'label': openapi.Schema(type=openapi.TYPE_STRING, description='Crop type label'),
                    },
                ),
            ),
        },
        security=[]
    )
    def get(self, request):
        crop_types = [{'value': value, 'label': label} for value, label in CropType.choices()]
        return Response(crop_types)

class RegisterFarmerView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description=(
            "Register a new farmer user and create their profile.\n\n"
            "**Permissions**: Public (no authentication required).\n"
            "**Request Body**:\n"
            "- `email`: Unique email address.\n"
            "- `username`: Unique username.\n"
            "- `password`: Password for the account.\n"
            "- `confirm_password`: Must match password.\n"
            "- `phone_number` (optional): Contact number.\n"
            "- `farm_location`: Location of the farm (e.g., city, region).\n"
            "- `farm_size`: Farm size in acres.\n"
            "- `crop_types` (optional): List of crops (e.g., `['MAIZE', 'WHEAT']`).\n\n"
            "**Returns**: User details (ID, email, username, role, etc.) and farmer profile details."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='Unique email address'),
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Unique username'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password', description='Account password'),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, format='password', description='Must match password'),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Contact number'),
                'farm_location': openapi.Schema(type=openapi.TYPE_STRING, description='Farm location (e.g., city, region)'),
                'farm_size': openapi.Schema(type=openapi.TYPE_NUMBER, format='float', description='Farm size in acres'),
                'crop_types': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING, enum=[ct.value for ct in CropType]),
                    nullable=True,
                    description='List of crop types (e.g., ["MAIZE", "WHEAT"])'
                ),
            },
            required=['email', 'username', 'password', 'confirm_password', 'farm_location', 'farm_size'],
        ),
        responses={
            201: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'user': openapi.Schema(type=openapi.TYPE_OBJECT, description='User details'),
                    'profile': openapi.Schema(type=openapi.TYPE_OBJECT, description='Farmer profile details'),
                },
            ),
            400: openapi.Schema(type=openapi.TYPE_OBJECT, description='Validation errors'),
        },
        security=[]
    )
    def post(self, request):
        serializer = RegisterFarmerSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.create(serializer.validated_data)
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterExpertView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description=(
            "Register a new expert user and create their profile.\n\n"
            "**Permissions**: Public (no authentication required).\n"
            "**Request Body**:\n"
            "- `email`: Unique email address.\n"
            "- `username`: Unique username.\n"
            "- `password`: Password for the account.\n"
            "- `phone_number` (optional): Contact number.\n"
            "- `areas_of_expertise`: Areas of specialization (e.g., 'Cassava, Maize').\n"
            "- `certifications` (optional): Professional certifications.\n"
            "- `bio` (optional): Short biography.\n"
            "- `experience_years` (optional): Years of experience.\n"
            "- `institution` (optional): Affiliated institution.\n"
            "- `languages_spoken` (optional): Spoken languages.\n"
            "- `social_links` (optional): Social media or professional links.\n\n"
            "**Returns**: User details (ID, email, username, role, etc.) and expert profile details."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='Unique email address'),
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Unique username'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password', description='Account password'),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Contact number'),
                'areas_of_expertise': openapi.Schema(type=openapi.TYPE_STRING, description='Areas of specialization'),
                'certifications': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Professional certifications'),
                'bio': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Short biography'),
                'experience_years': openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True, description='Years of experience'),
                'institution': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Affiliated institution'),
                'languages_spoken': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Spoken languages'),
                'social_links': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Social media/professional links'),
            },
            required=['email', 'username', 'password', 'areas_of_expertise'],
        ),
        responses={
            201: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'user': openapi.Schema(type=openapi.TYPE_OBJECT, description='User details'),
                    'profile': openapi.Schema(type=openapi.TYPE_OBJECT, description='Expert profile details'),
                },
            ),
            400: openapi.Schema(type=openapi.TYPE_OBJECT, description='Validation errors'),
        },
        security=[]
    )
    def post(self, request):
        serializer = RegisterExpertSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.create(serializer.validated_data)
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FarmerProfileView(APIView):
    permission_classes = [IsFarmer]

    @swagger_auto_schema(
        operation_description=(
            "Retrieve the authenticated farmer's profile.\n\n"
            "**Permissions**: Farmers only.\n"
            "**Returns**: Farmer profile details (farm location, size, crop types, etc.)."
        ),
        responses={
            200: FarmerProfileSerializer,
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        profile = request.user.farmer_profile
        serializer = FarmerProfileSerializer(profile)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description=(
            "Update the authenticated farmer's profile.\n\n"
            "**Permissions**: Farmers only.\n"
            "**Request Body**: Partial or full profile data (e.g., farm_location, farm_size, crop_types).\n"
            "**Returns**: Updated farmer profile details."
        ),
        request_body=FarmerProfileSerializer,
        responses={
            200: FarmerProfileSerializer,
            400: openapi.Schema(type=openapi.TYPE_OBJECT, description='Validation errors'),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def put(self, request):
        profile = request.user.farmer_profile
        serializer = FarmerProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ExpertProfileView(APIView):
    permission_classes = [IsExpert]

    @swagger_auto_schema(
        operation_description=(
            "Retrieve the authenticated expert's profile.\n\n"
            "**Permissions**: Experts only.\n"
            "**Returns**: Expert profile details (areas of expertise, certifications, bio, etc.)."
        ),
        responses={
            200: ExpertProfileSerializer,
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        profile = request.user.expert_profile
        serializer = ExpertProfileSerializer(profile)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description=(
            "Update the authenticated expert's profile.\n\n"
            "**Permissions**: Experts only.\n"
            "**Request Body**: Partial or full profile data (e.g., areas_of_expertise, bio, certifications).\n"
            "**Returns**: Updated expert profile details."
        ),
        request_body=ExpertProfileSerializer,
        responses={
            200: ExpertProfileSerializer,
            400: openapi.Schema(type=openapi.TYPE_OBJECT, description='Validation errors'),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def put(self, request):
        profile = request.user.expert_profile
        serializer = ExpertProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DiseaseHistoryView(APIView):
    permission_classes = [IsFarmer]
    pagination_class = PageNumberPagination

    @swagger_auto_schema(
        operation_description=(
            "Retrieve the authenticated farmer's disease detection history from the image analysis microservice.\n\n"
            "**Permissions**: Farmers only.\n"
            "**Returns**: Paginated list of disease detections (e.g., rust class, timestamp)."
        ),
        responses={
            200: openapi.Schema(type=openapi.TYPE_OBJECT, description='Paginated disease detection history'),
            400: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Microservice error')}),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        try:
            response = requests.get('http://localhost:8000/api/rust-detection/', headers={'Authorization': f'Bearer {request.auth}'})
            response.raise_for_status()
            detections = response.json()
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(detections, request)
            return paginator.get_paginated_response(page)
        except requests.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CropHealthAlertView(APIView):
    permission_classes = [IsFarmer]

    @swagger_auto_schema(
        operation_description=(
            "Check for crop health alerts based on disease detection frequency.\n\n"
            "**Permissions**: Farmers only.\n"
            "**Behavior**: If more than 5 common rust detections are found and no alert was sent in the last 24 hours, an email alert is sent.\n"
            "**Returns**: Status of alert check, number of common rust detections, and whether an alert was sent."
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='Alert check status'),
                    'common_rust_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of common rust detections'),
                    'alert_sent': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Whether an alert was sent'),
                },
            ),
            400: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Microservice or data error')}),
            500: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Email sending error')}),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        try:
            response = requests.get(
                'http://localhost:8000/api/rust-detection/',
                headers={'Authorization': f'Bearer {request.auth}'},
                timeout=5
            )
            response.raise_for_status()
            detections = response.json()

            if not isinstance(detections, list):
                logger.error("Invalid detection data format")
                return Response({'error': 'Invalid detection data'}, status=status.HTTP_400_BAD_REQUEST)

            common_rust_count = sum(1 for d in detections if d.get('rust_class') == 'common_rust')
            alert_sent = False

            if common_rust_count > 5:
                recent_alert = RustAlert.objects.filter(
                    farmer=request.user,
                    sent_at__gte=timezone.now() - timedelta(hours=24)
                ).exists()
                if not recent_alert:
                    subject = 'Crop Health Alert: Common Rust Detected'
                    message = (
                        f"Dear {request.user.username},\n\n"
                        f"We have detected common rust on your farm {common_rust_count} times.\n"
                        f"Please take immediate action to address this issue.\n"
                        f"Contact an agricultural expert via our platform if needed.\n"
                    )
                    try:
                        send_mail(
                            subject=subject,
                            message=message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[request.user.email],
                            fail_silently=False,
                        )
                        RustAlert.objects.create(
                            farmer=request.user,
                            detection_count=common_rust_count
                        )
                        alert_sent = True
                        logger.info(f"Sent common rust alert to {request.user.email}: {common_rust_count} detections")
                    except Exception as e:
                        logger.error(f"Failed to send alert to {request.user.email}: {str(e)}")
                        return Response({'error': f'Failed to send email: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                'status': 'Checked for alerts',
                'common_rust_count': common_rust_count,
                'alert_sent': alert_sent
            }, status=status.HTTP_200_OK)

        except requests.RequestException as e:
            logger.error(f"Failed to fetch detections: {str(e)}")
            return Response({'error': f'Failed to fetch detection data: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

class CommunityPostView(APIView):
    permission_classes = [IsFarmerOrAdmin]
    pagination_class = PageNumberPagination

    @swagger_auto_schema(
        operation_description=(
            "Retrieve a list of approved community posts, optionally filtered by disease type, crop type, or urgency level.\n\n"
            "**Permissions**: Farmers and admins.\n"
            "**Query Parameters**:\n"
            "- `disease_type` (optional): Filter by disease (e.g., `common_rust`, `leaf_blast`, `gray_leaf_spot`, `none`).\n"
            "- `crop_type` (optional): Filter by crop (e.g., `MAIZE`, `WHEAT`, `RICE`, `BEANS`, `POTATOES`).\n"
            "- `urgency_level` (optional): Filter by urgency (e.g., `low`, `medium`, `high`).\n"
            "- `page` (optional): Page number for pagination.\n"
            "- `page_size` (optional): Number of results per page.\n\n"
            "**Returns**: Paginated list of approved posts with title, content, farmer comments, and expert comments."
        ),
        manual_parameters=[
            openapi.Parameter('disease_type', openapi.IN_QUERY, description="Filter by disease type", type=openapi.TYPE_STRING, enum=[dt.value for dt in DiseaseType]),
            openapi.Parameter('crop_type', openapi.IN_QUERY, description="Filter by crop type", type=openapi.TYPE_STRING, enum=[ct.value for ct in CropType]),
            openapi.Parameter('urgency_level', openapi.IN_QUERY, description="Filter by urgency level", type=openapi.TYPE_STRING, enum=[ul.value for ul in UrgencyLevel]),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Results per page", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: CommunityPostSerializer(many=True),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        disease_type = request.query_params.get('disease_type')
        crop_type = request.query_params.get('crop_type')
        urgency_level = request.query_params.get('urgency_level')
        posts = CommunityPost.objects.filter(is_approved=True).order_by('-created_at')
        #apply filters if provieed
        if disease_type:
            posts = posts.filter(disease_type=disease_type)
        if crop_type:
            posts = posts.filter(crop_type=crop_type)
        if urgency_level:
            posts = posts.filter(urgency_level=urgency_level)
        # Initialize paginator
        paginator = self.pagination_class()
         # Paginate the queryset
        page = paginator.paginate_queryset(posts, request)
      
        # If page exists, serialize and return paginated response
        if page is not None:
            serializer = CommunityPostSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        # If no page (shouldn't happen with proper pagination params)
        serializer = CommunityPostSerializer(posts, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description=(
            "Create a new community post. Posts must be approved by an expert or admin before becoming visible.\n\n"
            "**Permissions**: Farmers only.\n"
            "**Request Body**:\n"
            "- `title`: Post title (max 200 characters).\n"
            "- `content`: Post content (text).\n"
            "- `disease_type`: Disease type (e.g., `common_rust`, `leaf_blast`, `gray_leaf_spot`, `none`).\n"
            "- `crop_type`: Crop type (e.g., `MAIZE`, `WHEAT`, `RICE`, `BEANS`, `POTATOES`).\n"
            "- `urgency_level`: Urgency level (e.g., `low`, `medium`, `high`).\n\n"
            "**Points**: Farmers earn 5 points for creating a post.\n"
            "**Returns**: The created post with initial status (`is_approved=false`, `is_flagged=false`)."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description='Post title (max 200 characters)'),
                'content': openapi.Schema(type=openapi.TYPE_STRING, description='Post content'),
                'disease_type': openapi.Schema(type=openapi.TYPE_STRING, enum=[dt.value for dt in DiseaseType], description='Disease type'),
                'crop_type': openapi.Schema(type=openapi.TYPE_STRING, enum=[ct.value for ct in CropType], description='Crop type'),
                'urgency_level': openapi.Schema(type=openapi.TYPE_STRING, enum=[ul.value for ul in UrgencyLevel], description='Urgency level'),
            },
            required=['title', 'content', 'disease_type', 'crop_type', 'urgency_level'],
        ),
        responses={
            201: CommunityPostSerializer,
            400: openapi.Schema(type=openapi.TYPE_OBJECT, description='Validation errors'),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def post(self, request):
        if request.user.role != 'farmer':
            return Response({'error': 'Only farmers can post'}, status=status.HTTP_403_FORBIDDEN)
        serializer = CommunityPostSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Community post created by {request.user.email}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CommunityResponseView(APIView):
    permission_classes = [IsFarmerOrAdmin]

    @swagger_auto_schema(
        operation_description=(
            "Retrieve all approved responses to a specific approved community post, separated into farmer and expert comments.\n\n"
            "**Permissions**: Farmers and admins.\n"
            "**Path Parameter**:\n"
            "- `post_id`: UUID of the approved post.\n\n"
            "**Returns**: Post details with `farmer_comments` and `expert_comments`."
        ),
        responses={
            200: CommunityPostSerializer,
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
            404: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Post not found or not approved')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request, post_id):
        try:
            post = CommunityPost.objects.get(id=post_id, is_approved=True)
            serializer = CommunityPostSerializer(post)
            return Response(serializer.data)
        except CommunityPost.DoesNotExist:
            return Response({'error': 'Post not found or not approved'}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description=(
            "Create a response to a specific approved community post. Responses must be approved by an expert before becoming visible.\n\n"
            "**Permissions**: Farmers only.\n"
            "**Path Parameter**:\n"
            "- `post_id`: UUID of the approved post.\n"
            "**Request Body**:\n"
            "- `content`: Response content (text).\n\n"
            "**Points**: Farmers earn 3 points for posting a response.\n"
            "**Returns**: The created response with initial approval status (`false`)."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'content': openapi.Schema(type=openapi.TYPE_STRING, description='Response content'),
            },
            required=['content'],
        ),
        responses={
            201: CommunityResponseSerializer,
            400: openapi.Schema(type=openapi.TYPE_OBJECT, description='Validation errors'),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
            404: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Post not found or not approved')}),
        },
        security=[{'Bearer': []}]
    )
    def post(self, request, post_id):
        if request.user.role != 'farmer':
            return Response({'error': 'Only farmers can respond'}, status=status.HTTP_403_FORBIDDEN)
        try:
            post = CommunityPost.objects.get(id=post_id, is_approved=True)
            data = request.data.copy()
            data['post'] = str(post.id)
            serializer = CommunityResponseSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Community response created by {request.user.email} for post {post_id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CommunityPost.DoesNotExist:
            return Response({'error': 'Post not found or not approved'}, status=status.HTTP_404_NOT_FOUND)

class CommunityPostModerationView(APIView):
    permission_classes = [IsExpertOrAdmin]

    @swagger_auto_schema(
        operation_description=(
            "Retrieve a list of unapproved community posts for moderation.\n\n"
            "**Permissions**: Experts and admins.\n"
            "**Returns**: Paginated list of posts with `is_approved=false`, including title, content, and other details."
        ),
        responses={
            200: CommunityPostSerializer(many=True),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        posts = CommunityPost.objects.filter(is_approved=False)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = CommunityPostSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description=(
            "Moderate a specific community post by approving, flagging, or unflagging it.\n\n"
            "**Permissions**: Experts and admins.\n"
            "**Path Parameter**:\n"
            "- `post_id`: UUID of the post to moderate.\n"
            "**Request Body**:\n"
            "- `action`: Action to perform (`approve`, `flag`, or `unflag`).\n\n"
            "**Effects**:\n"
            "- `approve`: Sets `is_approved=true`, making the post visible.\n"
            "- `flag`: Sets `is_flagged=true`, marking the post for review.\n"
            "- `unflag`: Sets `is_flagged=false`, clearing the flag.\n\n"
            "**Returns**: The updated post with its new approval/flagged status."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['approve', 'flag', 'unflag'], description='Action to perform'),
            },
            required=['action'],
        ),
        responses={
            200: CommunityPostSerializer,
            400: openapi.Schema(type=openapi.TYPE_OBJECT, description='Invalid action'),
            404: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Post not found')}),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def put(self, request, post_id):
        try:
            post = CommunityPost.objects.get(id=post_id)
            action = request.data.get('action')
            if action == 'approve':
                post.is_approved = True
                post.is_flagged = False  # Clear flag on approval
            elif action == 'flag':
                post.is_flagged = True
            elif action == 'unflag':
                post.is_flagged = False
            else:
                return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
            post.save()
            return Response(CommunityPostSerializer(post).data)
        except CommunityPost.DoesNotExist:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

class AllCommunityPostsView(APIView):
    permission_classes = [IsExpertOrAdmin]  # Note: This restricts access to experts and admins only
    pagination_class = PageNumberPagination

    def get(self, request):
        disease_type = request.query_params.get('disease_type')
        crop_type = request.query_params.get('crop_type')
        urgency_level = request.query_params.get('urgency_level')
        
        # Start with all posts
        posts = CommunityPost.objects.all().order_by('-created_at')  # Added ordering
        
        # Apply filters if provided
        if disease_type:
            posts = posts.filter(disease_type=disease_type)
        if crop_type:
            posts = posts.filter(crop_type=crop_type)
        if urgency_level:
            posts = posts.filter(urgency_level=urgency_level)
        
        # Paginate the results
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(posts, request)
        
        if page is not None:
            serializer = CommunityPostSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        # If pagination didn't return a page (empty queryset)
        serializer = CommunityPostSerializer(posts, many=True)
        return Response({
            'count': posts.count(),
            'next': None,
            'previous': None,
            'results': serializer.data
        })

class FlaggedCommunityPostsView(APIView):
    permission_classes = [IsExpertOrAdmin]
    pagination_class = PageNumberPagination

    @swagger_auto_schema(
        operation_description=(
            "Retrieve a list of flagged community posts for moderation.\n\n"
            "**Permissions**: Experts and admins.\n"
            "**Query Parameters**:\n"
            "- `disease_type` (optional): Filter by disease (e.g., `common_rust`, `leaf_blast`, `gray_leaf_spot`, `none`).\n"
            "- `crop_type` (optional): Filter by crop (e.g., `MAIZE`, `WHEAT`, `RICE`, `BEANS`, `POTATOES`).\n"
            "- `urgency_level` (optional): Filter by urgency (e.g., `low`, `medium`, `high`).\n"
            "- `page` (optional): Page number for pagination.\n"
            "- `page_size` (optional): Number of results per page.\n\n"
            "**Returns**: Paginated list of flagged posts with title, content, farmer comments, and expert comments."
        ),
        manual_parameters=[
            openapi.Parameter('disease_type', openapi.IN_QUERY, description="Filter by disease type", type=openapi.TYPE_STRING, enum=[dt.value for dt in DiseaseType]),
            openapi.Parameter('crop_type', openapi.IN_QUERY, description="Filter by crop type", type=openapi.TYPE_STRING, enum=[ct.value for ct in CropType]),
            openapi.Parameter('urgency_level', openapi.IN_QUERY, description="Filter by urgency level", type=openapi.TYPE_STRING, enum=[ul.value for ul in UrgencyLevel]),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Results per page", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: CommunityPostSerializer(many=True),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        disease_type = request.query_params.get('disease_type')
        crop_type = request.query_params.get('crop_type')
        urgency_level = request.query_params.get('urgency_level')
        posts = CommunityPost.objects.filter(is_flagged=True)
        if disease_type:
            posts = posts.filter(disease_type=disease_type)
        if crop_type:
            posts = posts.filter(crop_type=crop_type)
        if urgency_level:
            posts = posts.filter(urgency_level=urgency_level)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(posts, request)
        serializer = CommunityPostSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

class FarmerCommunityPostsView(APIView):
    permission_classes = [IsFarmerOrAdmin]
    pagination_class = PageNumberPagination

    @swagger_auto_schema(
        operation_description=(
            "Retrieve a list of community posts by a specific farmer, including status (Approved, Pending, Flagged).\n\n"
            "**Permissions**: Farmers (own posts only) and admins.\n"
            "**Path Parameter**:\n"
            "- `farmer_id`: UUID of the farmer.\n"
            "**Query Parameters**:\n"
            "- `disease_type` (optional): Filter by disease (e.g., `common_rust`, `leaf_blast`, `gray_leaf_spot`, `none`).\n"
            "- `crop_type` (optional): Filter by crop (e.g., `MAIZE`, `WHEAT`, `RICE`, `BEANS`, `POTATOES`).\n"
            "- `urgency_level` (optional): Filter by urgency (e.g., `low`, `medium`, `high`).\n"
            "- `page` (optional): Page number for pagination.\n"
            "- `page_size` (optional): Number of results per page.\n\n"
            "**Returns**: Paginated list of posts with status, title, content, farmer comments, and expert comments."
        ),
        manual_parameters=[
            openapi.Parameter('disease_type', openapi.IN_QUERY, description="Filter by disease type", type=openapi.TYPE_STRING, enum=[dt.value for dt in DiseaseType]),
            openapi.Parameter('crop_type', openapi.IN_QUERY, description="Filter by crop type", type=openapi.TYPE_STRING, enum=[ct.value for ct in CropType]),
            openapi.Parameter('urgency_level', openapi.IN_QUERY, description="Filter by urgency level", type=openapi.TYPE_STRING, enum=[ul.value for ul in UrgencyLevel]),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Results per page", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: CommunityPostSerializer(many=True),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
            404: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Farmer not found')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request, farmer_id):
        try:
            farmer = User.objects.get(id=farmer_id, role='farmer')
            if request.user.role != 'admin' and request.user.id != farmer_id:
                return Response({'error': 'You can only view your own posts'}, status=status.HTTP_403_FORBIDDEN)
            disease_type = request.query_params.get('disease_type')
            crop_type = request.query_params.get('crop_type')
            urgency_level = request.query_params.get('urgency_level')
            posts = CommunityPost.objects.filter(farmer=farmer)
            if disease_type:
                posts = posts.filter(disease_type=disease_type)
            if crop_type:
                posts = posts.filter(crop_type=crop_type)
            if urgency_level:
                posts = posts.filter(urgency_level=urgency_level)
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(posts, request)
            serializer = CommunityPostSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except User.DoesNotExist:
            return Response({'error': 'Farmer not found'}, status=status.HTTP_404_NOT_FOUND)

class FarmerPostCountView(APIView):
    permission_classes = [IsFarmerOrAdmin]

    @swagger_auto_schema(
        operation_description=(
            "Retrieve the number of community posts made by a specific farmer.\n\n"
            "**Permissions**: Farmers (own count only) and admins.\n"
            "**Path Parameter**:\n"
            "- `farmer_id`: UUID of the farmer.\n\n"
            "**Returns**: Farmer ID and total post count."
        ),
        responses={
            200: FarmerPostCountSerializer,
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
            404: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Farmer not found')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request, farmer_id):
        try:
            farmer = User.objects.get(id=farmer_id, role='farmer')
            if request.user.role != 'admin' and request.user.id != farmer_id:
                return Response({'error': 'You can only view your own post count'}, status=status.HTTP_403_FORBIDDEN)
            post_count = CommunityPost.objects.filter(farmer=farmer).count()
            data = {'farmer_id': farmer_id, 'post_count': post_count}
            serializer = FarmerPostCountSerializer(data)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({'error': 'Farmer not found'}, status=status.HTTP_404_NOT_FOUND)

class PointTransactionView(APIView):
    permission_classes = [IsFarmer]

    @swagger_auto_schema(
        operation_description=(
            "Retrieve the point transaction history for the authenticated farmer.\n\n"
            "**Permissions**: Farmers only.\n"
            "**Points System**:\n"
            "- Creating a post: +5 points.\n"
            "- Posting a response: +3 points.\n"
            "- Response approved by an expert: +10 points.\n\n"
            "**Returns**: A list of transactions with points, reason, and timestamp."
        ),
        responses={
            200: PointTransactionSerializer(many=True),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        transactions = PointTransaction.objects.filter(user=request.user)
        serializer = PointTransactionSerializer(transactions, many=True)
        return Response(serializer.data)

class EducationalContentSubmissionView(APIView):
    permission_classes = [IsExpert]

    @swagger_auto_schema(
        operation_description=(
            "Submit educational content to the education microservice.\n\n"
            "**Permissions**: Experts only.\n"
            "**Request Body**:\n"
            "- `title`: Content title.\n"
            "- `url`: URL to the content.\n"
            "- `description`: Content description.\n"
            "- `disease`: Related disease (e.g., common_rust).\n"
            "- `resource_type`: Type of resource (e.g., Article, Video).\n\n"
            "**Returns**: Response from the education microservice with content details."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description='Content title'),
                'url': openapi.Schema(type=openapi.TYPE_STRING, format='uri', description='Content URL'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Content description'),
                'disease': openapi.Schema(type=openapi.TYPE_STRING, description='Related disease'),
                'resource_type': openapi.Schema(type=openapi.TYPE_STRING, description='Resource type (e.g., Article, Video)'),
            },
            required=['title', 'url', 'description', 'disease', 'resource_type'],
        ),
        responses={
            201: openapi.Schema(type=openapi.TYPE_OBJECT, description='Response from education microservice'),
            400: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Microservice error')}),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def post(self, request):
        data = {
            'title': request.data.get('title'),
            'url': request.data.get('url'),
            'description': request.data.get('description'),
            'disease': request.data.get('disease'),
            'resource_type': request.data.get('resource_type'),
        }
        try:
            response = requests.post('http://localhost:8001/api/resources/', json=data, headers={'Authorization': f'Bearer {request.auth}'})
            response.raise_for_status()
            return Response(response.json(), status=status.HTTP_201_CREATED)
        except requests.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10  # Default page size
    page_size_query_param = 'page_size'  # Allows client to override page size
    max_page_size = 100  # Maximum limit for page size





class AvailabilitySlotView(APIView):
    permission_classes = [IsExpert]
    pagination_class = StandardResultsSetPagination

    @property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)

    @swagger_auto_schema(
        operation_description=(
            "Retrieve a paginated list of active, unbooked availability slots for the authenticated expert.\n\n"
            "**Permissions**: Experts only.\n"
            "**Pagination**:\n"
            "- Use `page` query parameter to specify page number\n"
            "- Use `page_size` query parameter to specify items per page (max 100)\n\n"
            "**Returns**: A paginated list of unbooked slots with start/end times and expert details."
        ),
        manual_parameters=[
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description="Number of items per page (max 100)",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            200: openapi.Response(
                'Paginated list of availability slots',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'start_time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                    'end_time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                    'is_booked': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    # Add other fields from your serializer here
                                }
                            )
                        )
                    }
                )
            ),
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        slots = AvailabilitySlot.objects.filter(
            expert=request.user,
            is_booked=False,
            is_active=True,
            end_time__gt=timezone.now()
        ).order_by('start_time')
        
        page = self.paginate_queryset(slots)
        if page is not None:
            serializer = AvailabilitySlotSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = AvailabilitySlotSerializer(slots, many=True)
        return Response(serializer.data)


    @swagger_auto_schema(
        operation_description=(
            "Create a new availability slot for the authenticated expert.\n\n"
            "**Permissions**: Experts only.\n"
            "**Request Body**:\n"
            "- `start_time`: Slot start time (ISO 8601 format).\n"
            "- `end_time`: Slot end time (ISO 8601 format).\n\n"
            "**Returns**: The created slot with details."
        ),
        request_body=AvailabilitySlotSerializer,
        responses={
            201: AvailabilitySlotSerializer,
            400: openapi.Schema(type=openapi.TYPE_OBJECT, description='Validation errors'),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def post(self, request):
        serializer = AvailabilitySlotSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            slot = serializer.save()
            logger.info(f"Availability slot created by {request.user.email}: {slot.id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EndAvailabilitySlotView(APIView):
    permission_classes = [IsExpert]

    @swagger_auto_schema(
        operation_description=(
            "End (deactivate) a specific availability slot.\n\n"
            "**Permissions**: Experts only.\n"
            "**Path Parameter**:\n"
            "- `slot_id`: UUID of the slot to end.\n\n"
            "**Returns**: Confirmation message."
        ),
        responses={
            200: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')}),
            400: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Slot is booked or already inactive')}),
            404: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Slot not found')}),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def put(self, request, slot_id):
        try:
            slot = AvailabilitySlot.objects.get(id=slot_id, expert=request.user)
            if slot.is_booked:
                return Response({'error': 'Cannot end a booked slot'}, status=status.HTTP_400_BAD_REQUEST)
            if not slot.is_active:
                return Response({'error': 'Slot is already inactive'}, status=status.HTTP_400_BAD_REQUEST)
            slot.is_active = False
            slot.save()
            logger.info(f"Availability slot {slot_id} ended by {request.user.email}")
            return Response({'message': 'Slot ended successfully'}, status=status.HTTP_200_OK)
        except AvailabilitySlot.DoesNotExist:
            return Response({'error': 'Slot not found'}, status=status.HTTP_404_NOT_FOUND)
        
class AllAvailabilitySlotsView(APIView):
    permission_classes = [IsFarmer]

    @swagger_auto_schema(
        operation_description=(
            "Retrieve a list of all active, unbooked availability slots with expert details.\n\n"
            "**Permissions**: Farmers only.\n"
            "**Query Parameters**:\n"
            "- `expert_id` (optional): Filter by expert UUID.\n"
            "- `crop_type` (optional): Filter by expert's areas of expertise matching crop type.\n"
            "**Returns**: A list of slots with start/end times and expert profile details."
        ),
        manual_parameters=[
            openapi.Parameter('expert_id', openapi.IN_QUERY, description="Filter by expert UUID", type=openapi.TYPE_STRING, format='uuid'),
            openapi.Parameter('crop_type', openapi.IN_QUERY, description="Filter by crop type", type=openapi.TYPE_STRING, enum=[ct.value for ct in CropType]),
        ],
        responses={
            200: AvailabilitySlotSerializer(many=True),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        slots = AvailabilitySlot.objects.filter(
            is_booked=False,
            is_active=True,
            end_time__gt=timezone.now()
        )
        expert_id = request.query_params.get('expert_id')
        crop_type = request.query_params.get('crop_type')
        if expert_id:
            slots = slots.filter(expert__id=expert_id)
        if crop_type:
            slots = slots.filter(expert__expert_profile__areas_of_expertise__icontains=crop_type)
        serializer = AvailabilitySlotSerializer(slots, many=True)
        return Response(serializer.data)

class ConsultationBookingView(APIView):
    permission_classes = [IsFarmer]

    @swagger_auto_schema(
        operation_description=(
            "Retrieve a list of consultation bookings for the authenticated farmer.\n\n"
            "**Permissions**: Farmers only.\n"
            "**Returns**: A list of bookings with slot, status, and selected date."
        ),
        responses={
            200: ConsultationBookingSerializer(many=True),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        bookings = ConsultationBooking.objects.filter(farmer=request.user)
        serializer = ConsultationBookingSerializer(bookings, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description=(
            "Create a new consultation booking for an available slot.\n\n"
            "**Permissions**: Farmers only.\n"
            "**Request Body**:\n"
            "- `slot_id`: UUID of an unbooked, active availability slot.\n\n"
            "**Returns**: The created booking with details."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'slot_id': openapi.Schema(type=openapi.TYPE_STRING, format='uuid', description='ID of the availability slot'),
            },
            required=['slot_id'],
        ),
        responses={
            201: ConsultationBookingSerializer,
            400: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Slot unavailable or invalid')}),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def post(self, request):
        slot_id = request.data.get('slot_id')
        try:
            slot = AvailabilitySlot.objects.get(id=slot_id, is_booked=False, is_active=True)
            if slot.is_expired():
                return Response({'error': 'Slot has expired'}, status=status.HTTP_400_BAD_REQUEST)
            booking = ConsultationBooking(farmer=request.user, slot=slot, status='pending')
            slot.is_booked = True
            slot.save()
            booking.save()
            serializer = ConsultationBookingSerializer(booking)
            logger.info(f"Booking {booking.id} created by {request.user.email} for slot {slot_id}")
            # Create in-app notification for farmer
            Notification.objects.create(
                user=request.user,
                message=f"Your booking (ID: {booking.id}) with {slot.expert.email} is pending approval."
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except AvailabilitySlot.DoesNotExist:
            return Response({'error': 'Slot unavailable or invalid'}, status=status.HTTP_400_BAD_REQUEST)


class BookingManagementView(APIView):
    permission_classes = [IsExpert]

    @swagger_auto_schema(
        operation_description=(
            "Retrieve a list of pending consultation bookings for the authenticated expert.\n\n"
            "**Permissions**: Experts only.\n"
            "**Returns**: A list of pending bookings with farmer and slot details."
        ),
        responses={
            200: ConsultationBookingSerializer(many=True),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        bookings = ConsultationBooking.objects.filter(
            slot__expert=request.user,
            status='pending'
        )
        serializer = ConsultationBookingSerializer(bookings, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description=(
            "Approve or reject a consultation booking with an optional selected date.\n\n"
            "**Permissions**: Experts only.\n"
            "**Request Body**:\n"
            "- `booking_id`: UUID of the booking to manage.\n"
            "- `action`: `approve` or `reject`.\n"
            "- `selected_date` (required for approve): Consultation date/time (ISO 8601 format).\n\n"
            "**Effects**:\n"
            "- Approve: Sets status to `approved`, saves selected date, sends notifications.\n"
            "- Reject: Sets status to `rejected`, sends notifications, frees slot.\n"
            "**Returns**: The updated booking."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'booking_id': openapi.Schema(type=openapi.TYPE_STRING, format='uuid', description='ID of the booking'),
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['approve', 'reject'], description='Action to perform'),
                'selected_date': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Selected consultation date (required for approve)'),
            },
            required=['booking_id', 'action'],
        ),
        responses={
            200: ConsultationBookingSerializer,
            400: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Invalid action or missing date')}),
            404: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Booking not found')}),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def put(self, request):
        booking_id = request.data.get('booking_id')
        action = request.data.get('action')
        selected_date_str = request.data.get('selected_date')

        try:
            booking = ConsultationBooking.objects.get(
                id=booking_id,
                slot__expert=request.user,
                status='pending'
            )
            if action == 'approve':
                if not selected_date_str:
                    return Response({'error': 'Selected date is required for approval'}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    # Try parsing with Django's parse_datetime (expects ISO 8601 or similar)
                    selected_date = django_parse_datetime(selected_date_str)
                    if selected_date is None:
                        # Fallback to dateutil.parser for flexible parsing
                        selected_date = parse_datetime(selected_date_str)
                    # Ensure the datetime is timezone-aware
                    if not timezone.is_aware(selected_date):
                        # Assume UTC if no timezone is provided
                        selected_date = timezone.make_aware(selected_date, timezone=dt_timezone.utc)
                    if selected_date < timezone.now():
                        return Response({'error': 'Selected date cannot be in the past'}, status=status.HTTP_400_BAD_REQUEST)
                except ValueError:
                    return Response({'error': 'Invalid date format. Use ISO 8601 (e.g., "2025-08-04T17:57:00Z") or "YYYY-MM-DD HH:MM:SS"'}, status=status.HTTP_400_BAD_REQUEST)
                booking.status = 'approved'
                booking.selected_date = selected_date
            elif action == 'reject':
                booking.status = 'rejected'
                booking.slot.is_booked = False
                booking.slot.save()
            else:
                return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

            booking.notification_sent = True
            booking.save()

            # Create in-app notification
            message = (
                f"Your booking (ID: {booking.id}) with {request.user.email} has been {booking.status}."
                f"{' Scheduled for ' + booking.selected_date.strftime('%Y-%m-%d %H:%M') if booking.status == 'approved' else ''}"
            )
            Notification.objects.create(
                user=booking.farmer,
                message=message
            )

            # Send email notification synchronously
            subject = f"Consultation Booking {booking.status.capitalize()}"
            email_message = (
                f"Dear {booking.farmer.username},\n\n"
                f"Your consultation booking (ID: {booking.id}) with expert {request.user.username} ({request.user.email}) has been {booking.status}.\n"
            )
            if booking.status == 'approved' and booking.selected_date:
                email_message += (
                    f"The consultation is scheduled for {booking.selected_date.strftime('%Y-%m-%d %H:%M')}.\n"
                    f"Please contact the expert via phone or WhatsApp at {booking.slot.expert.phone_number} to coordinate.\n"
                )


            try:
                send_mail(
                    subject=subject,
                    message=email_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[booking.farmer.email],
                    fail_silently=False,
                )
                logger.info(f"Sent {booking.status} notification email to {booking.farmer.email} for booking {booking.id}")
            except Exception as e:
                logger.error(f"Failed to send {booking.status} email to {booking.farmer.email}: {str(e)}")
                # Optionally return an error response if email sending fails
                return Response(
                    {'error': f'Failed to send notification email: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            logger.info(f"Booking {booking_id} {action}d by {request.user.email}")
            return Response(ConsultationBookingSerializer(booking).data)

        except ConsultationBooking.DoesNotExist:
            return Response({'error': 'Booking not found or not pending'}, status=status.HTTP_404_NOT_FOUND)     




class UserManagementView(APIView):
    permission_classes = [IsAdmin]

    @swagger_auto_schema(
        operation_description=(
            "Retrieve a list of all users in the system.\n\n"
            "**Permissions**: Admins only.\n"
            "**Returns**: A list of users with details (ID, email, username, role, approval status, etc.)."
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_STRING, format='uuid', description='User ID'),
                        'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='User email'),
                        'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                        'role': openapi.Schema(type=openapi.TYPE_STRING, enum=['farmer', 'expert', 'admin'], description='User role'),
                        'is_approved': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Approval status'),
                        'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Active status'),
                        'phone_number': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Phone number'),
                    },
                ),
            ),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description=(
            "Update a specific user's details or perform an action (approve/block).\n\n"
            "**Permissions**: Admins only.\n"
            "**Path Parameter**:\n"
            "- `user_id`: UUID of the user to update.\n"
            "**Request Body**:\n"
            "- `action` (optional): `approve` (sets `is_approved=true`) or `block` (sets `is_approved=false`, `is_active=false`).\n"
            "- `email` (optional): Updated email.\n"
            "- `username` (optional): Updated username.\n"
            "- `role` (optional): Updated role (`farmer`, `expert`, `admin`).\n"
            "- `is_approved` (optional): Approval status.\n"
            "- `is_active` (optional): Active status.\n\n"
            "**Returns**: The updated user details."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['approve', 'block'], description='Action to perform (optional)'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='User email (optional)'),
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username (optional)'),
                'role': openapi.Schema(type=openapi.TYPE_STRING, enum=['farmer', 'expert', 'admin'], description='User role (optional)'),
                'is_approved': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Approval status (optional)'),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Active status (optional)'),
            },
        ),
        responses={
            200: UserSerializer,
            400: openapi.Schema(type=openapi.TYPE_OBJECT, description='Validation errors'),
            404: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='User not found')}),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def put(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            action = request.data.get('action')
            if action == 'approve':
                user.is_approved = True
            elif action == 'block':
                user.is_approved = False
                user.is_active = False
            else:
                serializer = UserSerializer(user, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            user.save()
            return Response(UserSerializer(user).data)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class SystemHealthView(APIView):
    permission_classes = [IsAdmin]

    @swagger_auto_schema(
        operation_description=(
            "Retrieve system performance metrics.\n\n"
            "**Permissions**: Admins only.\n"
            "**Returns**: A list of metrics with names, values, and timestamps."
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_STRING, format='uuid', description='Metric ID'),
                        'metric_name': openapi.Schema(type=openapi.TYPE_STRING, description='Metric name'),
                        'value': openapi.Schema(type=openapi.TYPE_NUMBER, format='float', description='Metric value'),
                        'recorded_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Metric timestamp'),
                    },
                ),
            ),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        metrics = SystemMetric.objects.all()
        serializer = SystemMetricSerializer(metrics, many=True)
        return Response(serializer.data)

class ModelRetrainingView(APIView):
    permission_classes = [IsAdmin]

    @swagger_auto_schema(
        operation_description=(
            "Trigger retraining of the disease detection model in the image analysis microservice.\n\n"
            "**Permissions**: Admins only.\n"
            "**Request Body**: Training data (format depends on the image analysis microservice).\n"
            "**Returns**: Confirmation that retraining was triggered."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description='Training data (format depends on image analysis microservice)',
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'status': openapi.Schema(type=openapi.TYPE_STRING, description='Retraining status')},
            ),
            400: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Microservice error')}),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def post(self, request):
        try:
            response = requests.post('http://localhost:8000/api/upload-training-images/', data=request.data, headers={'Authorization': f'Bearer {request.auth}'})
            response.raise_for_status()
            return Response({'status': 'Retraining triggered'}, status=status.HTTP_200_OK)
        except requests.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class FeedbackAnalysisView(APIView):
    permission_classes = [IsAdmin]

    @swagger_auto_schema(
        operation_description=(
            "Retrieve a summary of user feedback.\n\n"
            "**Permissions**: Admins only.\n"
            "**Returns**: Total feedback count and count of feedback from the last 30 days."
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'total_feedback': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total feedback count'),
                    'recent_feedback': openapi.Schema(type=openapi.TYPE_INTEGER, description='Feedback count in last 30 days'),
                },
            ),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        feedback = Feedback.objects.all()
        total = feedback.count()
        recent = feedback.filter(created_at__gte=timezone.now() - timedelta(days=30)).count()
        return Response({'total_feedback': total, 'recent_feedback': recent})

class ContentApprovalView(APIView):
    permission_classes = [IsAdmin]

    @swagger_auto_schema(
        operation_description=(
            "Retrieve a list of unapproved community posts for admin approval.\n\n"
            "**Permissions**: Admins only.\n"
            "**Returns**: A list of posts with `is_approved=false`."
        ),
        responses={
            200: CommunityPostSerializer(many=True),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        posts = CommunityPost.objects.filter(is_approved=False)
        serializer = CommunityPostSerializer(posts, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description=(
            "Approve or reject a specific community post.\n\n"
            "**Permissions**: Admins only.\n"
            "**Path Parameter**:\n"
            "- `post_id`: UUID of the post to approve/reject.\n"
            "**Request Body**:\n"
            "- `is_approved`: Boolean to approve (`true`) or reject (`false`) the post.\n\n"
            "**Returns**: The updated post with its new approval status."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'is_approved': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Approval status')},
        ),
        responses={
            200: CommunityPostSerializer,
            404: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Post not found')}),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def put(self, request, post_id):
        try:
            post = CommunityPost.objects.get(id=post_id)
            post.is_approved = request.data.get('is_approved', False)
            post.save()
            return Response(CommunityPostSerializer(post).data)
        except CommunityPost.DoesNotExist:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description=(
            "Reset a user's password using a valid reset token.\n\n"
            "**Permissions**: Public (no authentication required).\n"
            "**Request Body**:\n"
            "- `token`: Password reset token received via email.\n"
            "- `new_password`: New password.\n"
            "- `confirm_password`: Must match new password.\n\n"
            "**Returns**: Confirmation message on successful password reset."
        ),
        request_body=ResetPasswordSerializer,
        responses={
            200: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')}),
            400: openapi.Schema(type=openapi.TYPE_OBJECT, description='Validation errors or expired/invalid token'),
            404: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Invalid token')}),
        },
        security=[]
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            try:
                reset_token = PasswordResetToken.objects.get(token=serializer.validated_data['token'])
                if not reset_token.is_valid():
                    reset_token.delete()
                    return Response({'error': 'Token has expired'}, status=status.HTTP_400_BAD_REQUEST)
                user = reset_token.user
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                reset_token.delete()
                return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)
            except PasswordResetToken.DoesNotExist:
                return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description=(
            "Request a password reset email with a token.\n\n"
            "**Permissions**: Public (no authentication required).\n"
            "**Request Body**:\n"
            "- `email`: Email address of the user.\n\n"
            "**Returns**: Confirmation message that a reset email was sent."
        ),
        request_body=ForgotPasswordSerializer,
        responses={
            200: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')}),
            400: openapi.Schema(type=openapi.TYPE_OBJECT, description='Validation errors or user not found'),
            500: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Email sending error')}),
        },
        security=[]
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            token = str(uuid.uuid4())
            expires_at = timezone.now() + timedelta(hours=1)

            PasswordResetToken.objects.create(
                user=user,
                token=token,
                expires_at=expires_at
            )

            reset_url = f"{settings.FRONTEND_URL}/auth/confirm-password-reset?token={token}"
            subject = 'Password Reset Request'
            message = (
                f"Hi {user.username},\n\n"
                f"You requested a password reset. Click the link below to set a new password:\n"
                f"{reset_url}\n\n"
                f"This link will expire in 1 hour.\n"
                f"If you didn't request this, please ignore this email.\n"
            )
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as e:
                return Response({'error': f'Failed to send email: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({'message': 'Password reset email sent'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = [IsExpert, IsFarmer]

    @swagger_auto_schema(
        operation_description=(
            "Change the authenticated user's password.\n\n"
            "**Permissions**: Farmers and experts.\n"
            "**Request Body**:\n"
            "- `old_password`: Current password.\n"
            "- `new_password`: New password.\n"
            "- `confirm_password`: Must match new password.\n\n"
            "**Returns**: Confirmation message on successful password change."
        ),
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')}),
            400: openapi.Schema(type=openapi.TYPE_OBJECT, description='Validation errors or incorrect old password'),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def put(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FarmerByIdView(APIView):
    permission_classes = [IsAdmin]

    @swagger_auto_schema(
        operation_description=(
            "Retrieve a specific farmer's profile by ID.\n\n"
            "**Permissions**: Admins only.\n"
            "**Path Parameter**:\n"
            "- `id`: UUID of the farmer.\n\n"
            "**Returns**: Farmer profile details (farm location, size, crop types, etc.)."
        ),
        responses={
            200: FarmerProfileSerializer,
            404: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Farmer not found')}),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request, id):
        try:
            farmer_profile = FarmerProfile.objects.get(user__id=id, user__role='farmer')
            serializer = FarmerProfileSerializer(farmer_profile)
            return Response(serializer.data)
        except FarmerProfile.DoesNotExist:
            return Response({'error': 'Farmer not found'}, status=status.HTTP_404_NOT_FOUND)

class ExpertByIdView(APIView):
    permission_classes = [IsAdmin]

    @swagger_auto_schema(
        operation_description=(
            "Retrieve a specific expert's profile by ID.\n\n"
            "**Permissions**: Admins only.\n"
            "**Path Parameter**:\n"
            "- `id`: UUID of the expert.\n\n"
            "**Returns**: Expert profile details (areas of expertise, certifications, bio, etc.)."
        ),
        responses={
            200: ExpertProfileSerializer,
            404: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Expert not found')}),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request, id):
        try:
            expert_profile = ExpertProfile.objects.get(user__id=id, user__role='expert')
            serializer = ExpertProfileSerializer(expert_profile)
            return Response(serializer.data)
        except ExpertProfile.DoesNotExist:
            return Response({'error': 'Expert not found'}, status=status.HTTP_404_NOT_FOUND)
        
class ExpertResponseModerationView(APIView):
    permission_classes = [IsExpert]

    @swagger_auto_schema(
        operation_description=(
            "Retrieve all unapproved responses for a specific approved post.\n\n"
            "**Permissions**: Experts only.\n"
            "**Path Parameter**:\n"
            "- `post_id`: UUID of the approved post.\n\n"
            "**Returns**: List of unapproved responses with content and farmer details."
        ),
        responses={
            200: CommunityResponseSerializer(many=True),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
            404: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Post not found or not approved')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request, post_id):
        try:
            post = CommunityPost.objects.get(id=post_id, is_approved=True)
            responses = post.responses.filter(is_approved=False)
            serializer = CommunityResponseSerializer(responses, many=True)
            return Response(serializer.data)
        except CommunityPost.DoesNotExist:
            return Response({'error': 'Post not found or not approved'}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description=(
            "Approve or reject a specific response with optional expert comment.\n\n"
            "**Permissions**: Experts only.\n"
            "**Path Parameters**:\n"
            "- `post_id`: UUID of the post (for URL consistency)\n"
            "- `response_id`: UUID of the response to moderate (in request body)\n\n"
            "**Request Body**:\n"
            "- `response_id`: UUID of the response to moderate\n"
            "- `action`: 'approve' or 'reject'\n"
            "- `expert_comment`: Optional comment from expert\n\n"
            "**Effects**:\n"
            "- Approving: Marks as approved, adds comment, awards 10 points to farmer\n"
            "- Rejecting: Marks as rejected, adds comment\n\n"
            "**Returns**: The updated response"
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'response_id': openapi.Schema(type=openapi.TYPE_STRING, format='uuid', description='ID of response to moderate'),
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['approve', 'reject'], description='Action to perform'),
                'expert_comment': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description='Optional expert comment'),
            },
            required=['response_id', 'action'],
        ),
        responses={
            200: CommunityResponseSerializer,
            400: openapi.Schema(type=openapi.TYPE_OBJECT, description='Invalid action or missing parameters'),
            404: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Response not found')}),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def put(self, request, post_id):
        try:
            # First verify the post exists and is approved
            post = CommunityPost.objects.get(id=post_id, is_approved=True)
            
            # Get the response to moderate from request body
            response_id = request.data.get('response_id')
            if not response_id:
                return Response({'error': 'response_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            response = post.responses.get(id=response_id)
            action = request.data.get('action')
            expert_comment = request.data.get('expert_comment', '')

            if action == 'approve':
                response.is_approved = True
                response.expert_comment = expert_comment
                response.approved_by = request.user
                response.save()
                
                # Award points to farmer
                user = response.farmer
                user.points += 10
                user.save()
                PointTransaction.objects.create(
                    user=user, 
                    points=10, 
                    reason="Response approved by expert"
                )
                
                # Increment expert's validated count
                expert_profile = request.user.expert_profile
                expert_profile.validated_responses_count += 1
                expert_profile.save()

            elif action == 'reject':
                response.is_approved = False
                response.expert_comment = expert_comment
                response.approved_by = request.user
                response.save()

            else:
                return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

            return Response(CommunityResponseSerializer(response).data)

        except CommunityPost.DoesNotExist:
            return Response({'error': 'Post not found or not approved'}, status=status.HTTP_404_NOT_FOUND)
        except CommunityResponse.DoesNotExist:
            return Response({'error': 'Response not found for this post'}, status=status.HTTP_404_NOT_FOUND)


class CommunityPostByIdView(APIView):
    permission_classes = [IsExpertOrAdmin | IsFarmerOrAdmin]
    @swagger_auto_schema(
        operation_description=(
            "Retrieve a specific community post by its ID.\n\n"
            "**Permissions**:\n"
            "- Farmers can view approved posts or their own posts (approved or unapproved).\n"
            "- Experts and admins can view any post (approved or unapproved).\n"
            "**Path Parameter**:\n"
            "- `post_id`: UUID of the post.\n\n"
            "**Returns**: Post details including title, content, farmer, farmer comments, and expert comments."
        ),
        responses={
            200: CommunityPostSerializer,
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
            404: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Post not found')}),
        },
        security=[{'Bearer': []}]
    )

    def get(self, request, post_id):
        try:
            post = CommunityPost.objects.get(id=post_id)
            # Check permissions
            if request.user.role == 'farmer' and not post.is_approved and post.farmer != request.user:
                return Response(
                    {'error': 'You can only view approved posts or your own posts'},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = CommunityPostSerializer(post)
            logger.info(f"Post {post_id} retrieved by {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CommunityPost.DoesNotExist:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)


@shared_task
def send_booking_notification_email(farmer_email, expert_email, booking_id, status, selected_date=None):
    subject = f"Consultation Booking {status.capitalize()}"
    message = (
        f"Dear Farmer,\n\n"
        f"Your consultation booking (ID: {booking_id}) with expert {expert_email} has been {status}.\n"
    )
    if status == 'approved' and selected_date:
        message += f"The consultation is scheduled for {selected_date.strftime('%Y-%m-%d %H:%M')}.\n"
    message += "Log in to the platform for more details.\n"
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[farmer_email],
            fail_silently=False,
        )
        logger.info(f"Sent {status} notification email to {farmer_email} for booking {booking_id}")
    except Exception as e:
        logger.error(f"Failed to send {status} email to {farmer_email}: {str(e)}")

class NotificationView(APIView):
    permission_classes = [IsFarmer]

    @swagger_auto_schema(
        operation_description=(
            "Retrieve a list of notifications for the authenticated farmer.\n\n"
            "**Permissions**: Farmers only.\n"
            "**Query Parameters**:\n"
            "- `is_read` (optional): Filter by read status (`true` or `false`).\n"
            "**Returns**: A list of notifications with message and read status."
        ),
        manual_parameters=[
            openapi.Parameter('is_read', openapi.IN_QUERY, description="Filter by read status", type=openapi.TYPE_BOOLEAN),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_STRING, format='uuid', description='Notification ID'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Notification message'),
                        'is_read': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Read status'),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Creation time'),
                    },
                ),
            ),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        is_read = request.query_params.get('is_read')
        if is_read is not None:
            notifications = notifications.filter(is_read=is_read.lower() == 'true')
        return Response([
            {
                'id': n.id,
                'message': n.message,
                'is_read': n.is_read,
                'created_at': n.created_at
            } for n in notifications
        ])

    @swagger_auto_schema(
        operation_description=(
            "Mark a notification as read.\n\n"
            "**Permissions**: Farmers only.\n"
            "**Path Parameter**:\n"
            "- `notification_id`: UUID of the notification to mark as read.\n\n"
            "**Returns**: Confirmation message."
        ),
        responses={
            200: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')}),
            404: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Notification not found')}),
            401: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')}),
            403: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description='Forbidden')}),
        },
        security=[{'Bearer': []}]
    )
    def put(self, request, notification_id):
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.is_read = True
            notification.save()
            return Response({'message': 'Notification marked as read'})
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
        
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class: type[CustomTokenObtainPairSerializer] = CustomTokenObtainPairSerializer
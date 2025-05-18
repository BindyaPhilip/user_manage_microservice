from django.urls import path, include
from .views import (
    AllAvailabilitySlotsView, AllCommunityPostsView, BookingManagementView, EndAvailabilitySlotView, FarmerCommunityPostsView, FarmerPostCountView, FlaggedCommunityPostsView, NotificationView, RegisterFarmerView, RegisterExpertView, FarmerProfileView, ExpertProfileView,
    DiseaseHistoryView, CropHealthAlertView, CommunityPostView, CommunityPostModerationView,
    CommunityResponseView, ExpertResponseModerationView, PointTransactionView,
    EducationalContentSubmissionView, AvailabilitySlotView, ConsultationBookingView,
    UserManagementView, SystemHealthView, ModelRetrainingView, FeedbackAnalysisView,
    ContentApprovalView, ExpertByIdView, FarmerByIdView,
    ChangePasswordView, ForgotPasswordView, ResetPasswordView, CropTypeView,ExpertResponseModerationView,CommunityPostByIdView
)

# Authentication endpoints
auth_urls = [
    path('register/farmer/', RegisterFarmerView.as_view(), name='register-farmer'),
    path('register/expert/', RegisterExpertView.as_view(), name='register-expert'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
]

# User management endpoints
user_urls = [
    path('farmer-profile/', FarmerProfileView.as_view(), name='farmer-profile'),
    path('expert-profile/', ExpertProfileView.as_view(), name='expert-profile'),
    path('farmer/<uuid:id>/', FarmerByIdView.as_view(), name='farmer-by-id'),
    path('expert/<uuid:id>/', ExpertByIdView.as_view(), name='expert-by-id'),
    path('users/', UserManagementView.as_view(), name='user-management'),
    path('users/<uuid:user_id>/', UserManagementView.as_view(), name='user-management-detail'),
]

# Community feature endpoints
community_urls = [
    path('posts/', CommunityPostView.as_view(), name='community-posts'),  # Approved posts
    path('posts/all/', AllCommunityPostsView.as_view(), name='all-community-posts'),
    path('posts/flagged/', FlaggedCommunityPostsView.as_view(), name='flagged-community-posts'),
    path('posts/farmer/<uuid:farmer_id>/', FarmerCommunityPostsView.as_view(), name='farmer-community-posts'),
    path('posts/farmer/<uuid:farmer_id>/count/', FarmerPostCountView.as_view(), name='farmer-post-count'),
    path('posts/moderate/<uuid:post_id>/', CommunityPostModerationView.as_view(), name='community-post-moderate'),
    path('responses/<uuid:post_id>/', CommunityResponseView.as_view(), name='community-responses'),
    path('responses/moderate/<uuid:post_id>/', ExpertResponseModerationView.as_view(), name='community-response-moderate'),
    path('points/', PointTransactionView.as_view(), name='point-transactions'),
    path('posts/<uuid:post_id>/', CommunityPostByIdView.as_view(), name='community-post-detail')
]

# Consultation service endpoints
consultation_urls = [
    path('availability-slots/', AvailabilitySlotView.as_view(), name='availability-slots'),
    path('availability-slots/all/', AllAvailabilitySlotsView.as_view(), name='all-availability-slots'),
    path('availability-slots/end/<uuid:slot_id>/', EndAvailabilitySlotView.as_view(), name='end-availability-slot'),
    path('consultations/', ConsultationBookingView.as_view(), name='consultations'),
    path('consultations/manage/', BookingManagementView.as_view(), name='manage-bookings'),
    path('notifications/', NotificationView.as_view(), name='notifications'),
    path('notifications/<uuid:notification_id>/', NotificationView.as_view(), name='notification-detail'),
]

# Crop health and analysis endpoints
crop_health_urls = [
    path('disease-history/', DiseaseHistoryView.as_view(), name='disease-history'),
    path('crop-health-alerts/', CropHealthAlertView.as_view(), name='crop-health-alerts'),
    path('retrain-model/', ModelRetrainingView.as_view(), name='retrain-model'),
]

# Content management endpoints
content_urls = [
    path('educational-content/', EducationalContentSubmissionView.as_view(), name='educational-content'),
    path('content-approval/<uuid:post_id>/', ContentApprovalView.as_view(), name='content-approval'),
]

# System monitoring endpoints
system_urls = [
    path('system-health/', SystemHealthView.as_view(), name='system-health'),
    path('feedback-analysis/', FeedbackAnalysisView.as_view(), name='feedback-analysis'),
]

# Miscellaneous endpoints
misc_urls = [
    path('crop-types/', CropTypeView.as_view(), name='crop-types'),
]

# Combine all URL patterns
urlpatterns = [
    path('auth/', include(auth_urls)),
    path('users/', include(user_urls)),
    path('community/', include(community_urls)),
    path('consultations/', include(consultation_urls)),
    path('crop-health/', include(crop_health_urls)),
    path('content/', include(content_urls)),
    path('system/', include(system_urls)),
    path('', include(misc_urls)),
]
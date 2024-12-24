from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('register/', views.register, name='register'),
    path('home/', views.home, name='home'),
    # path('add_business/', views.add_business, name='add_business'),
    # path('my_businesses/', views.view_my_businesses, name='my_businesses'),
    path('queue_management/', views.queue_management, name='queue_management'),
    path('business-list/', views.business_list, name='business_list'),
    path('appointment_booking/', views.appointment_booking, name='appointment_booking'),
    path('get_branch_details/', views.get_branch_details, name='get_branch_details'),  # Add this line
        path('book_appointment/', views.book_appointment, name='book_appointment'),
    path('get_booked_slots/', views.get_booked_slots, name='get_booked_slots'),


    path('my-businesses/', views.view_my_businesses, name='my_businesses'),
    path('view-customers/<str:branch_name>/', views.view_customers, name='view_customers'),
    path('add-business/', views.add_business, name='add_business'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


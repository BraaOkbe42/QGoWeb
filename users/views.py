from django.shortcuts import render, redirect
from .forms import RegistrationForm
from firebase_admin import auth
from .models import Business
from .forms import BusinessForm
from django.contrib.auth.views import LoginView

from django.contrib.auth import login  # Django's built-in login function

from django.contrib import messages
from django.contrib.auth.decorators import login_required
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Save the Django user first
                user = form.save()
                print(f"Attempting to create Firebase user with email: {user.email}")

                # Create a Firebase user
                firebase_user = auth.create_user(
                    email=user.email,
                    password=form.cleaned_data['password1']
                )
                print(f"Firebase user created successfully: {firebase_user.uid}")

                # Link the Firebase UID to the Django user
                user.firebase_uid = firebase_user.uid
                user.save()

                # Log in the user immediately after registration
                login(request, user)

                # Redirect to the home page
                messages.success(request, "Account created successfully.")
                return redirect('home')  # Redirect to the home page

            except Exception as e:
                print(f"Error creating Firebase user: {e}")
                form.add_error(None, f"An error occurred: {e}")
    else:
        form = RegistrationForm()

    return render(request, 'users/register.html', {'form': form})



def custom_login(request):  # Renamed this function
    return redirect('login')  # Redirect to the login page

class CustomLoginView(LoginView):
    template_name = 'users/login.html'

    
@login_required
def home(request):
    return render(request, 'home.html')

from django.shortcuts import render, redirect
from firebase_admin import firestore
from django.contrib.auth.decorators import login_required
from django.contrib import messages




@login_required
def add_business(request):
    db = firestore.client()
    user = request.user

    # Check if the user already has a business
    user_business = db.collection('businesses').where('user_id', '==', user.firebase_uid).stream()
    business_name = None
    for business in user_business:
        business_name = business.to_dict().get('business_name')
        break

    if request.method == "POST":
        if not business_name:  # Allow saving the business name only if it doesn't exist
            business_name = request.POST.get('business_name')
        branch_name = request.POST.get('branch_name')
        rating = request.POST.get('rating', None)  # Fetch the rating

        # Retrieve working hours dynamically
        working_hours = []
        for key in request.POST.keys():
            if key.startswith('from_time_'):
                index = key.split('_')[-1]
                from_time = request.POST.get(f'from_time_{index}')
                to_time = request.POST.get(f'to_time_{index}')
                days = request.POST.getlist(f'working_days_{index}')

                working_hours.append({
                    'from_time': from_time,
                    'to_time': to_time,
                    'days': days
                })

        # Save the branch details to Firestore
        db.collection('businesses').add({
            'user_id': user.firebase_uid,
            'business_name': business_name,
            'branch_name': branch_name,
            'working_hours': working_hours,
            'photo_url': request.FILES.get('photo'),  # Handle photo upload
            'rating': rating,  # Save the rating
        })

        messages.success(request, "Branch added successfully!")
        return redirect('home')

    return render(request, 'users/add_business.html', {'business_name': business_name})






# from django.db import models

# class Business(models.Model):
#     business_name = models.CharField(max_length=100)
#     branch_name = models.CharField(max_length=100)
#     photo = models.ImageField(upload_to='business_photos/', blank=True, null=True)
#     hours_of_operation = models.CharField(max_length=50)  # e.g., "8:00 to 17:00"
#     working_days = models.CharField(max_length=50)  # e.g., "Monday to Friday"
#     rating = models.DecimalField(
#         max_digits=3,  # Supports ratings like 4.5 or 10.0
#         decimal_places=1,
#         null=True,
#         blank=True,
#         help_text="Enter a rating between 0 and 10",
#     )

#     def __str__(self):
#         return f"{self.business_name} - {self.branch_name}"








@login_required
def view_my_businesses(request):
    db = firestore.client()
    user = request.user  # Get the currently logged-in user

    # Query Firestore for businesses that belong to this user
    businesses = db.collection('businesses').where('user_id', '==', user.firebase_uid).stream()

    # Convert Firestore documents to a list
    user_businesses = []
    for business in businesses:
        user_businesses.append(business.to_dict())

    return render(request, 'users/my_businesses.html', {'businesses': user_businesses})


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from firebase_admin import firestore

@login_required
def queue_management(request):
    db = firestore.client()

    # Query to fetch all appointments
    appointments_query = db.collection("appointments").stream()

    # Prepare appointment data
    appointments = []
    for appointment in appointments_query:
        appointment_data = appointment.to_dict()
        appointments.append({
            "customer_name": appointment_data.get("customer_name", "Anonymous"),
            "branch_name": appointment_data.get("branch_name"),
            "time": appointment_data.get("time"),
            "date": appointment_data.get("day")
        })

    # Pass appointments to the template
    return render(request, "users/queue_management.html", {"appointments": appointments})


from collections import defaultdict

@login_required
def business_list(request):
    db = firestore.client()

    # Fetch all businesses from Firestore
    businesses_query = db.collection('businesses').stream()

    # Group branches by business name with hours and days
    grouped_businesses = defaultdict(list)
    for business in businesses_query:
        business_data = business.to_dict()
        business_name = business_data.get('business_name')
        branch_info = {
            'branch_name': business_data.get('branch_name'),
            'working_hours': business_data.get('working_hours')  # List of dictionaries
        }
        grouped_businesses[business_name].append(branch_info)

    # Convert defaultdict to a regular list of dictionaries for the template
    businesses = [{'business_name': name, 'branches': branches} for name, branches in grouped_businesses.items()]

    return render(request, 'business_list.html', {'businesses': businesses})








from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from firebase_admin import firestore
from collections import defaultdict
from datetime import datetime, timedelta
from django.contrib import messages

@login_required
def appointment_booking(request):
    db = firestore.client()

    # Fetch all businesses and group branches under them
    businesses_query = db.collection('businesses').stream()

    businesses = {}
    for business in businesses_query:
        business_data = business.to_dict()
        business_name = business_data.get('business_name')
        if not business_name:
            continue  # Skip entries without a business name

        if business_name not in businesses:
            businesses[business_name] = []

        branch_info = {
            'branch_name': business_data.get('branch_name'),
            'working_hours': business_data.get('working_hours', [])
        }
        businesses[business_name].append(branch_info)

    return render(request, 'users/appointment_booking.html', {'businesses': businesses})

@login_required
def get_branch_details(request):
    if request.method == "POST":
        db = firestore.client()
        business_name = request.POST.get("business_name")
        print("Received business name:", business_name)

        branch_query = db.collection("businesses").where("business_name", "==", business_name).stream()
        branches = []

        for branch in branch_query:
            branch_data = branch.to_dict()
            print("Branch data fetched from Firestore:", branch_data)
            branches.append({
                "branch_name": branch_data.get("branch_name"),
                "working_hours": branch_data.get("working_hours", [])
            })

        print("Final branch list:", branches)
        return JsonResponse({"branches": branches})

    print("Invalid request method for get_branch_details.")
    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def book_appointment(request):
    if request.method == "POST":
        db = firestore.client()
        user = request.user
        business_name = request.POST.get("business_name")
        branch_name = request.POST.get("branch_name")
        day = request.POST.get("day")
        time = request.POST.get("time")

        # Check if the slot is already booked
        existing_appointments = db.collection("appointments").where("business_name", "==", business_name).where("branch_name", "==", branch_name).where("day", "==", day).where("time", "==", time).stream()

        if any(existing_appointments):
            return JsonResponse({"error": "This slot is already booked."}, status=409)

        # Save the appointment
        db.collection("appointments").add({
            "user_id": user.firebase_uid,
            "business_name": business_name,
            "branch_name": branch_name,
            "day": day,
            "time": time
        })

        return JsonResponse({"success": "Appointment booked successfully!"})

    return JsonResponse({"error": "Invalid request"}, status=400)



@login_required
def get_booked_slots(request):
    if request.method == "POST":
        db = firestore.client()
        branch_name = request.POST.get("branch_name")
        print("Received branch name for booked slots:", branch_name)

        appointments_query = db.collection("appointments").where("branch_name", "==", branch_name).stream()
        booked_slots = []

        for appointment in appointments_query:
            appointment_data = appointment.to_dict()
            print("Fetched appointment:", appointment_data)
            booked_slots.append({
                "day": appointment_data["day"],
                "time": appointment_data["time"]
            })

        print("Final booked slots list:", booked_slots)
        return JsonResponse({"booked_slots": booked_slots})

    print("Invalid request method for get_booked_slots.")
    return JsonResponse({"error": "Invalid request method"}, status=400)



# from django.shortcuts import render
# from firebase_admin import firestore
# from django.contrib.auth.decorators import login_required

# @login_required
# def view_customers(request, branch_name):
#     db = firestore.client()

#     # Query Firestore for appointments for the given branch
#     appointments_query = db.collection('appointments').where('branch_name', '==', branch_name).stream()

#     # Extract the appointment details directly from Firestore
#     appointments = []
#     for appointment in appointments_query:
#         data = appointment.to_dict()
#         appointments.append({
#             'customer_name': data.get('customer_name', 'Unknown'),
#             'appointment_date': data.get('day'),
#             'appointment_time': data.get('time'),  # Retrieve directly from Firestore
#         })

#     # Pass data to the template
#     return render(request, 'users/view_customers.html', {
#         'branch_name': branch_name,
#         'appointments': appointments
#     })

from django.shortcuts import render
from firebase_admin import firestore
from django.contrib.auth.decorators import login_required
from datetime import datetime
import pytz

@login_required
def view_customers(request, branch_name):
    db = firestore.client()

    # Define the desired time zone
    target_tz = pytz.timezone('Asia/Jerusalem')  # UTC+2

    # Query Firestore for appointments for the given branch
    appointments_query = db.collection('appointments').where('branch_name', '==', branch_name).stream()

    # Extract the appointment details and adjust time
    appointments = []
    for appointment in appointments_query:
        data = appointment.to_dict()

        # Handle the time field as DatetimeWithNanoseconds
        raw_time = data.get('time', None)
        if raw_time:
            try:
                # Convert Firestore DatetimeWithNanoseconds to Python datetime
                local_time = raw_time.astimezone(target_tz).strftime("%H:%M")
            except Exception as e:
                local_time = f"Error processing time: {str(e)}"
        else:
            local_time = "No time provided"

        # Add the processed data to the appointments list
        appointments.append({
            'customer_name': data.get('customer_name', 'Unknown'),
            'appointment_date': data.get('date', 'No date provided'),
            'appointment_time': local_time,  # Corrected time
        })

    # Pass data to the template
    return render(request, 'users/view_customers.html', {
        'branch_name': branch_name,
        'appointments': appointments
    })

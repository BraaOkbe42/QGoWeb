import firebase_admin
from firebase_admin import credentials, auth

# Initialize Firebase
cred = credentials.Certificate('firebase/firebase_key.json')
firebase_admin.initialize_app(cred)

# Test Firebase user creation
try:
    user = auth.create_user(
        email='testuser@example.com',
        password='examplepassword123'
    )
    print(f"Firebase user created: {user.uid}")
except Exception as e:
    print(f"Error: {e}")

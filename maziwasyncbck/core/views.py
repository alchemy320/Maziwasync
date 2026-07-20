from django.db import IntegrityError,transaction
from django.shortcuts import render
from rest_framework_simplejwt.exceptions import TokenError
from .models import FarmerProfile, PorterProfile, User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny,IsAdminUser,IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny,IsAdminUser,IsAuthenticated
from rest_framework.authentication import authenticate

from rest_framework.response import Response
from django.db import IntegrityError
from django.db import transaction

# Register view - accessible to anyone (no authentication required)
# Without @permission_classes([AllowAny]), the global IsAuthenticated setting
# would block this endpoint, making it impossible to register a new account
@api_view(['POST'])  # only accepts POST requests
@permission_classes([IsAdminUser])  # overrides global IsAuthenticated for this view
@transaction.atomic  
def Register(request):
    # print("Register function ")
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    role = request.data.get('role', 'farmer')  # default role is 'farmer' if not provided
    phone_number = request.data.get('phone_number')
    # print(username, password, email, role, phone_number)  # logs received data to terminal

    if not username or not password or not email or not phone_number:
        return Response({"error": "Email,Username and Password are required"}, status=400)
    # check if the username or email already exists
    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already taken"}, status=400)
    if User.objects.filter(email=email).exists():
        return Response({"error": "Email already registered"}, status=400)
    
    try:
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            role=role,
            phone_number=phone_number
        )
        if role == 'farmer':
            farmer_profile = FarmerProfile.objects.create(
            user=user,
            phone_number=phone_number,
            first_name=request.data.get('first_name'),
            last_name=request.data.get('last_name'),
            national_id=request.data.get('national_id'),

            )
        elif role == 'porter':
            # Create a PorterProfile if the role is 'porter'
            porter_profile = PorterProfile.objects.create(
                user=user,
                phone_number=phone_number,
                first_name=request.data.get('first_name'),
                last_name=request.data.get('last_name'),
                national_id=request.data.get('national_id'),
                employee_id=request.data.get('employee_id'),
                route_name=request.data.get('route_name'),
                
            )
        return Response({
            "username": user.username,
            "user_id": user.id,
            "role": user.role,
            "message": f"{role.capitalize()} Registered successfully"
            
        })
        
        # error caught from the db
    except IntegrityError as e:
        return Response({"error": "Integrity Error" + str(e)})

    except Exception as e:
        return Response({"error": str(e)})


# Login
@api_view(["POST"])
@permission_classes([AllowAny])
def Login(request):
    username = request.data.get("username")
    password = request.data.get("password")
    # print(username,password)

    user=authenticate(username=username, password=password)
    if not user:
        return Response({"error": "Invalid credentials"})
    
    refresh=RefreshToken.for_user(user)

    return Response({
        "username": user.username,
        "role": user.role,
        "refresh": str(refresh),
        "access_token": str(refresh.access_token),
    })

# ==================================================
# Get user/profile of the logged in user
# ==================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def MyProfile(request):
    user=request.user
    print(user)

    profile_data={}
    if user.role=='farmer' and hasattr(user,'farmer_profile'):
        p=user.farmer_profile
        profile_data={
            'first_name': p.first_name,
            'last_name': p.last_name,
            'employee_id': p.employee_id,
            'farm_name': p.farm_name
        }
    elif user.role=='porter' and hasattr(user, 'porter_profile'):
        p=user.porter_profile
        profile_data={
            'first_name': p.first_name,
            'last_name': p.last_name,
            'employee_id': p.employee_id,
            'route_name': p.route_name
        }

    return Response({
        'id':user.id,
        'username': user.username,
        'role': user.role,
        'profile': profile_data
    })

# ===========
# Logout
# ==========
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def Logout(request):
    try:
       Refresh_Token = request.data['refresh']
       token = RefreshToken(Refresh_Token)
       token.blacklist()
       return Response({"message": "Successfully logged out"})
    except TokenError:
        return Response({"error": "Invalid or expired"})
    except Exception as e:
        return Response({"error": str(e)})



        
    
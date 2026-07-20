from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from django.shortcuts import render
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAuthenticated

from core.models import FarmerProfile, MilkCollection, Notice, PorterProfile
from rest_framework.response import Response
from rest_framework import generics

from collector.serializer import MilkCollectionSerializer
from cooperative.serializer import NoticeSerializer
# porters dashboard
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def PorterDashboard(request):
    # get the logged porter/user from the token
    try:
        porter = request.user.porter_profile
    except PorterProfile.DoesNotExist:
        return Response({"error": "Only porters can access this dashboard"})
    
    # time settings
    today= timezone.now().date()
    week_start=today-timedelta(days=7)
    month_start=today.replace(day=1)

    # Todays collections
    today_collections = MilkCollection.objects.filter(
        porter=porter,
        collection_date=today
    )
    total_collection_today = today_collections.count()
    total_litters_today = today_collections.aggregate(
        total=Sum("liters")
    )["total"] or 0
    total_amount_today = today_collections.aggregate(
        total=Sum("total_amount")
    )["total"] or 0

    # weekly/monthly
    weekly_collections = MilkCollection.objects.filter(
        porter=porter,
        collection_date__gte=week_start
    )
    total_liters_week = weekly_collections.aggregate(
        total=Sum("liters")
    )["total"] or 0

    monthly_collections = MilkCollection.objects.filter(
        porter=porter,
        collection_date__gte=month_start
    )
    total_liters_month = monthly_collections.aggregate(
        total=Sum("liters")
    )["total"] or 0

    # last 5 collections
    last_collections = MilkCollection.objects.filter(
        porter=porter
    ).order_by("-created_at")[:5]

    # serialize the last 5 collections queryset
    last_collections_data = MilkCollectionSerializer(last_collections, many=True).data

    return Response({
        'date': today,
        'assigned_farmers': porter.assigned_farmers.count(),
        'total_collection_today': total_collection_today,
        'total_litters_today': total_litters_today,
        'total_amount_today': total_amount_today,
        'total_liters_week': total_liters_week,
        'total_liters_month': total_liters_month,
        'last_collections': last_collections_data,
        'porter_name':f'{porter.first_name} {porter.last_name}',
        'route_name':porter.route_name,
        'employee_id':porter.employee_id,
        
        })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def AddMilkCollection(request):
    # get the logged in user - porter
    try:
        porter=request.user.porter_profile  
    except PorterProfile.DoesNotExist:
        return Response({"error": "Only porter can add milk collection"})
    
    # check if the farmer exist first then pick the object
    
    try:
        national_id = request.data.get('national_id')
        farmer = FarmerProfile.objects.get(national_id=national_id)
    except FarmerProfile.DoesNotExist:
        return Response({"error": "Farmer not found"})
    
    collection= MilkCollection.objects.create(
        porter=porter,
        farmer=farmer,
        liters=request.data.get('liters'),
        session=request.data.get('session'),
    )
    return Response({
        "message": "Milk collection recorded successfully",
        "collection_id": collection.id,
        "farmer":f"{farmer.first_name} {farmer.last_name}",
        "porter":f"{porter.first_name} {porter.last_name}",
        "liters":collection.liters
    })

# view porter collections list
class MyCollections(generics.ListAPIView):
    serializer_class = MilkCollectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        porter = self.request.user.porter_profile

        collections = (
            MilkCollection.objects
            .filter(porter=porter)
            .select_related("farmer")
            .order_by("created_at")
        )

        return collections
    
class PorterNoticeView(generics.ListAPIView):
    serializer_class = NoticeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        notices=(
            Notice.objects
            .filter(target__in=['ALL','PORTERS'])
            .order_by('-created_at')
        )
        return notices
    




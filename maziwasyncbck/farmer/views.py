from django.shortcuts import render
from rest_framework import generics, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum
from datetime import date, timedelta
from core.models import FarmerProfile, Feedback, MilkCollection, Notice
from farmer.serializer import MilkCollectionSerializer, FeedbackSerializer
from cooperative.serializer import NoticeSerializer
from farmer.services import CattleAIService
# Create your views here.

# Farmer dashboard
class FarmerDashboard(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        farmer= request.user.farmer_profile
        collection= MilkCollection.objects.filter(farmer=farmer)
        total_collection=collection.count()
        total_liter=collection.aggregate(total=Sum("liters"))["total"] or 0
        total_amount=collection.aggregate(total=Sum("total_amount"))["total"] or 0

        today_collection=collection.filter(collection_date=date.today()).aggregate(total=Sum('liters'))['total'] or 0

        monthly_liter=collection.filter(
            collection_date__month=timezone.now().month
        ).aggregate(total=Sum('liters'))['total'] or 0

        monthly_earning= collection.filter(
            collection_date__month=timezone.now().month
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        return Response({
            "total_collection":total_collection,
            "total_liter":total_liter,
            "total_amount":total_amount,
            "today_collection":today_collection,
            "monthly_liter":monthly_liter,
            "monthly_earning":monthly_earning,

        })
   

    

# farmer's milk collection
class farmerCollection(generics.ListAPIView):
    serializer_class = MilkCollectionSerializer
    permission_classes=[IsAuthenticated]

    # qyery set - fetdh data from the model in a class
    def get_queryset(self):
        # get the logged in user - farmer
        try:
            farmer=self.request.user.farmer_profile  
        except FarmerProfile.DoesNotExist:
            raise PermissionDenied(
                "only farmers can access this endpoint"
            )
        collections=(
            MilkCollection.objects
            .filter(farmer=farmer)
            .select_related("porter")
            .order_by("created_at")
        )
        return collections
    
# ==================
# feedback
# ==================
class feedbackViewset(viewsets.ModelViewSet):
    serializer_class=FeedbackSerializer
    permission_classes=[IsAuthenticated]
    
    def get_queryset(self):
        try:
            farmer=self.request.user.farmer_profile
        except:
            raise PermissionDenied("only farmers can access this endpoint")
        
        feedback=(
            Feedback.objects
            .filter(farmer=farmer)
            .order_by("created_at")
        )
        return feedback
    
    # post by the farmer token
    def perform_create(self, serializer):
        try:
            farmer=self.request.user.farmer_profile
        except:
            raise PermissionDenied("only farmers can create feedback")
        
        serializer.save(farmer=farmer)

        #notice
class FarmerNoticeView(generics.ListAPIView):
    serializer_class = NoticeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        notices=(
            Notice.objects
            .filter(target__in=['ALL','FARMERS'])
            .order_by('-created_at')
        )
        return notices
    
    # cattleAi function
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def PredictDisease(request):
    animal = request.data.get("Animal")
    age = request.data.get("Age")
    temp = request.data.get("Temperature")
    Description = request.data.get("Description")

    # create our ai object from the CattleAIService
    ai_service = CattleAIService()
    result = ai_service.predict(animal_type=animal, age=age, temp=temp, description=Description)
    return Response(result)




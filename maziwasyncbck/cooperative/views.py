from datetime import timedelta

from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

from rest_framework import viewsets

from cooperative.serializer import FarmerSerializer, NoticeSerializer
from core.models import FarmerProfile, Feedback, MilkCollection, Notice, Payment, PorterProfile
from collector.serializer import MilkCollectionSerializer
from django.utils import timezone
from django.db.models import Sum
from rest_framework.response import Response

from cooperative.services import MpesaPayment
from rest_framework.permissions import AllowAny
# Create your views here.

# admin/cooperative dashboard
class AdminDashboardView(APIView):
    # only admin can access this analystics dashboard
    permission_classes=[IsAdminUser]

    # method to get the analysitis
    def get(self,request):
        # define the dates according to django timezone settings
        # used for daily, weekly and monthly calculations
        today = timezone.localdate()
        # calculate the weekly which is 7days
        week_start = today - timedelta(days=7)

        # farmer and porter starts
        total_farmers=FarmerProfile.objects.count()
        total_porters=PorterProfile.objects.count()

        # milk collection starts
        # we retrive all the collection so that we can reuse 
        collections=MilkCollection.objects.all()

        total_liters=collections.aggregate(total=Sum("liters"))["total"] or 0
        today_liters=collections.filter( collection_date=today).aggregate(total=Sum("liters"))["total"] or 0

        # weekly collection
        weekly_liters=collections.filter(collection_date__gte=week_start).aggregate(total=Sum("liters"))["total"] or 0

        # monthly collection
        monthly_liters=collections.filter(
            collection_date__year=today.year,
            collection_date__month=today.month
        ).aggregate(total=Sum('liters'))['total'] or 0

        # total revenue
        total_revenue=collections.aggregate(total=Sum("total_amount"))["total"] or 0

        # today revenue
        today_revenue=collections.filter(collection_date=today).aggregate(total=Sum("total_amount"))["total"] or 0

        # this week revenue
        weekly_revenue=collections.filter(collection_date__gte=week_start).aggregate(total=Sum("total_amount"))["total"] or 0

        # this month revenue
        monthly_revenue=collections.filter(
            collection_date__year=today.year,
            collection_date__month=today.month
        ).aggregate(total=Sum("total_amount"))["total"] or 0

        # feedback analytics
        # resolved
        resolved_feedbacks=Feedback.objects.filter(status='RESOLVED').count()
        # pending
        pending_feedbacks=Feedback.objects.filter(status='PENDNG').count()

        # top Farmers- retrieve farmers with highest milk delivery
        top_farmers=FarmerProfile.objects.annotate(
            total_liters=Sum('collections__liters')
        ).order_by('-total_liters')[:5]
        
        # convert the farmerProfile objects into json
        top_farmers_data=FarmerSerializer(top_farmers, many=True).data 

        # top ten latest milk collections
        recent_collections=MilkCollection.objects.select_related(
            'farmer',
            'porter'
        ).order_by('-created_at')[:10]

        # convert the collection objects to JSON data
        recent_collections_data=MilkCollectionSerializer(recent_collections, many=True).data

        # Dashboard response
        # send all analytic data to frontend
        return Response({
            'total_farmers':total_farmers,
            'total_porters':total_porters,
            'total_liters':total_liters,
            'today_liters':today_liters,
            'weekly_liters':weekly_liters,
            'monthly_liters':monthly_liters,
            'total_revenue':total_revenue,
            'today_revenue':today_revenue,
            'weekly_revenue':weekly_revenue,
            'monthly_revenue':monthly_revenue,
            'resolved_feedbacks':resolved_feedbacks,
            'pending_feedbacks':pending_feedbacks,
            'top_farmers':top_farmers_data,
            'recent_collections':recent_collections_data
        })


        

class FarmerViewSet(viewsets.ModelViewSet):
    queryset=FarmerProfile.objects.all()
    serializer_class=FarmerSerializer
    permission_classes=[IsAdminUser]
    http_method_names=['get','patch','put','delete']

class PorterViewSet(viewsets.ModelViewSet): 
    queryset=FarmerProfile.objects.all()
    serializer_class=FarmerSerializer
    permission_classes=[IsAdminUser]
    http_method_names=['get','patch','put','delete']

class MilkCollectionViewSet(viewsets.ModelViewSet):
    queryset=MilkCollection.objects.select_related(
        'farmer',
        'porter'
    )
    serializer_class=MilkCollectionSerializer
    permission_classes=[IsAdminUser]
    http_method_names=['get','patch','put','delete']

# notices board by the cooperative
class NoticeViewSet(viewsets.ModelViewSet):
    queryset=Notice.objects.all()
    serializer_class=NoticeSerializer
    permission_classes=[IsAdminUser]

    def perform_create(self,serializer):
        serializer.save(created_by=self.request.user)


# get farmers with outstanding arrears/balances
@api_view(["GET"])
@permission_classes([IsAdminUser])
def FarmerWithBal(request):
    farmers=FarmerProfile.objects.all()
    data=[]
    for farmer in farmers:
        # amount earned by the farmer
        earned=MilkCollection.objects.filter(farmer=farmer).aggregate(
            total=Sum('total_amount')
        )['total'] or 0

        # amount paid to the farmer
        paid=Payment.objects.filter(farmer=farmer,status='COMPLETED').aggregate(
            total=Sum('amount')
        )['total'] or 0

        balance=earned-paid
        if balance > 0:
            data.append({
                "farmer_id":farmer.id,
                "farmer_name":f"{farmer.first_name} {farmer.last_name}",
                "balance":balance,
                "paid":paid,
                "earned":earned,
                "phone":farmer.phone_number
            })

    return Response(data)

# initiate the dusbursment ti the farmer
@api_view(["POST"])
@permission_classes([IsAdminUser])
def pay_farmer(request):
    farmer_id=request.data.get("farmer_id")
    amount=request.data.get("amount")

    farmer=FarmerProfile.objects.get(id=farmer_id)

    earned=MilkCollection.objects.filter(farmer=farmer).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    paid=Payment.objects.filter(farmer=farmer, status='COMPLETED').aggregate(
        total=Sum('amount')
    )['total'] or 0
    balance=earned-paid
    if balance <=0:
        return Response({"message":"No pending"})
    
    mpesa=MpesaPayment()
    result=mpesa.pay_farmer(farmer.phone_number, amount)

    # create the payment record
    Payment.objects.create(
        farmer=farmer,
        amount=amount,
        payment_method="MPESA",
        originator_conversation_id=result['OriginatorConversationID'],
        transaction_ref=result['ConversationID'],
        payment_date=timezone.now()
    )

    return Response({
        "Farmer": f"{farmer.first_name} {farmer.last_name}",
        "prev_balance": balance,
        "mpesa_response": result
    })

# asynchronous callback processing webhook
@api_view(["POST"])
@permission_classes([AllowAny])
def mpesa_callback(request):
    print("=====call back hit=====")
    data=request.data

    # print the response from safaricom to see it in the terminal
    print("data",data)
    result=data["Result"]

    originator_conversation_id=result["OriginatorConversationID"]

    # retrieve the matching payment record with the originator conversation id
    payment=Payment.objects.get (originator_conversation_id=originator_conversation_id)

    # check if the transaction was successfull
    if result["ResultCode"]==0:
        payment.status="COMPLETED"
    else:
        payment.status="FAILED"

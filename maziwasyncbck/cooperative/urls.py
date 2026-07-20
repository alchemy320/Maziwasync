from django.urls import path,include
from rest_framework.routers import DefaultRouter

from cooperative import views
router=DefaultRouter()
router.register('farmers', views.FarmerViewSet, basename='farmers')
router.register('porter',views.PorterViewSet, basename='porter')
router.register('milk-collections',views.MilkCollectionViewSet, basename='milk-collections')
router.register('notice', views.NoticeViewSet, basename='notice')

urlpatterns=[
    path('dashboard/', views.AdminDashboardView.as_view(), name='admin-dashboard'),
    path('farmers-balance/', views.FarmerWithBal, name='farmers-balance'),
    path('', include(router.urls)),
    path('payfarmer/', views.pay_farmer, name='pay-farmer'),
    path('',include(router.urls))
]
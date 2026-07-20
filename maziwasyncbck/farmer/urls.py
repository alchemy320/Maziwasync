from django.urls import path,include
from farmer import views
from rest_framework.routers import DefaultRouter



router=DefaultRouter()
router.register('feedback',views.feedbackViewset, basename='feedback')

urlpatterns=[
    path('collections/', views.farmerCollection.as_view()),
    path('dashboard/',views.farmerCollection.as_view()),
    path('',include(router.urls)),
    path('notice/',views.FarmerNoticeView.as_view()),
    path('predict/', views.PredictDisease)
]
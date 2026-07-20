from rest_framework import serializers

from core.models import Feedback, MilkCollection

# serializer for the farmer milk collection showing also the porter who collected the milk
class MilkCollectionSerializer(serializers.ModelSerializer):
    porter_name=serializers.SerializerMethodField()
    class Meta:
        model = MilkCollection
        fields = ['id','collection_date', 'liters', 'total_amount','porter_name','price_per_liter','session']

        # serializer for the farmer milk collection showing also the porter who collected the milk

# method to just join the firstname and last name of the porter to be one name

# use it when you want to alter the field on how it look like in the model
    def get_porter_name(self,obj):
        return obj.porter.first_name+" "+obj.porter.last_name
    
    # feedback serialiser
class FeedbackSerializer(serializers.ModelSerializer):
     class Meta:
            model = Feedback
            fields = ['id','title', 'description','status','created_at','updated_at']
            read_only_fields=['status','created_at','updated_at']

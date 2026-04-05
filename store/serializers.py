from rest_framework import serializers
from .models import User, Store, Product ,Expense

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'store']

class RegisterStoreSerializer(serializers.Serializer):
    # Data za Duka
    store_name = serializers.CharField()
    phone = serializers.CharField()
    # Data za Mmiliki
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        # 1. Tengeneza Duka
        store = Store.objects.create(
            name=validated_data['store_name'],
            phone=validated_data['phone']
        )
        # 2. Tengeneza Mmiliki
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            role='owner',
            store=store
        )
        return user
class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['id', 'store', 'description', 'amount', 'date']
        # Muhimu: Store iweze kuwa optional wakati wa kuserialize 
        # kwa sababu tunaijaza kwenye view
        extra_kwargs = {'store': {'required': False}}
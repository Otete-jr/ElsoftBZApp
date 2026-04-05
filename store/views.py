from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import Store, Sale, Product,Expense
from .serializers import RegisterStoreSerializer, UserSerializer, StoreSerializer, ExpenseSerializer, ProductSerializer
from django.utils import timezone
from datetime import datetime
from django.db.models import Sum
from django.db.models.functions import ExtractMonth, ExtractYear
from django.utils.dateparse import parse_date

@api_view(['POST'])
def register_store(request):
    serializer = RegisterStoreSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "user": UserSerializer(user).data,
            "message": "Duka limesajiliwa kikamilifu!"
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "user": UserSerializer(user).data,
            "store": StoreSerializer(user.store).data if user.store else None
        })
    return Response({"error": "Username au Password si sahihi"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_expenses(request):
    user_store = request.user.store
    
    if request.method == 'GET':
        expenses = Expense.objects.filter(store=user_store).order_by('-date')
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        data = request.data.copy()
        data['store'] = user_store.id # Tunamkabidhi ID ya duka lake hapa
        
        serializer = ExpenseSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        
        # ANGALIA HAPA: Hii itakuambia kosa ni nini kwenye terminal
        print("Expense Errors:", serializer.errors) 
        return Response(serializer.errors, status=400)
    
@api_view(['POST'])
def make_sale(request):
    product_id = request.data.get('product_id')
    quantity = int(request.data.get('quantity', 1))
    sold_at_price = request.data.get('sold_at_price') # Bei uliyomuuzia mteja

    try:
        product = Product.objects.get(id=product_id)
        if product.stock >= quantity:
            product.stock -= quantity
            product.save()
            
            # Tunatumia bei iliyotoka kwenye simu (baada ya discount)
            total = float(sold_at_price) * quantity
            
            Sale.objects.create(
                store=product.store,
                product=product,
                quantity=quantity,
                total_price=total
            )
            return Response({"message": "Mauzo yamekamilika!"}, status=201)
        else:
            return Response({"error": "Stoko haitoshi!"}, status=400)
    except Exception as e:
        return Response({"error": str(e)}, status=400)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_products(request):
    user_store = request.user.store

    # 1. KAMA MTUMIAJI ANATAKA KUONA BIDHAA (GET)
    if request.method == 'GET':
        products = Product.objects.filter(store=user_store).order_by('-id')
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    # 2. KAMA MTUMIAJI ANASAJILI BIDHAA MPYA (POST)
    elif request.method == 'POST':
        data = request.data.copy()
        data['store'] = user_store.id # Ambatanisha duka la huyu aliyelogin
        
        serializer = ProductSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        # Kama kuna makosa (mfano bei siyo namba), yarudishe
        print("Product Errors:", serializer.errors) # Utaona kosa kwenye Terminal
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_detailed_reports(request):
    user_store = request.user.store
    # Pata tarehe inayotoka kwenye simu, la sivyo tumia ya leo
    date_str = request.query_params.get('date')
    if date_str:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        target_date = timezone.now().date()

    # --- 1. RIPOTI YA SIKU HUSIKA ---
    daily_sales = Sale.objects.filter(store=user_store, sale_date__date=target_date)
    daily_expenses = Expense.objects.filter(store=user_store, date=target_date)

    # Orodha ya bidhaa zilizouzwa leo
    sold_items = []
    total_daily_sales = 0
    total_daily_cost = 0 # Mtaji wa bidhaa zilizouzwa

    for sale in daily_sales:
        total_daily_sales += sale.total_price
        total_daily_cost += (sale.product.buying_price * sale.quantity)
        sold_items.append({
            "name": sale.product.name,
            "qty": sale.quantity,
            "total": float(sale.total_price)
        })

    total_daily_expenses = daily_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    expenses_list = [{"desc": e.description, "amount": float(e.amount)} for e in daily_expenses]

    # --- 2. RIPOTI YA MWEZI HUU ---
    month_sales_qs = Sale.objects.filter(store=user_store, sale_date__month=target_date.month, sale_date__year=target_date.year)
    month_exp_qs = Expense.objects.filter(store=user_store, date__month=target_date.month, date__year=target_date.year)

    total_month_sales = month_sales_qs.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_month_expenses = month_exp_qs.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Mtaji wa mwezi (kwa bidhaa zilizouzwa tu)
    total_month_cost = sum(s.product.buying_price * s.quantity for s in month_sales_qs)

    # --- 3. RIPOTI YA MWAKA HUU ---
    year_sales = Sale.objects.filter(store=user_store, sale_date__year=target_date.year).aggregate(Sum('total_price'))['total_price__sum'] or 0
    year_expenses = Expense.objects.filter(store=user_store, date__year=target_date.year).aggregate(Sum('amount'))['amount__sum'] or 0
    year_cost = sum(s.product.buying_price * s.quantity for s in Sale.objects.filter(store=user_store, sale_date__year=target_date.year))

    return Response({
        "daily": {
            "items": sold_items,
            "total_sales": float(total_daily_sales),
            "expenses": expenses_list,
            "total_expenses": float(total_daily_expenses),
            "net_cash": float(total_daily_sales - total_daily_expenses),
            "profit": float(total_daily_sales - total_daily_cost - total_daily_expenses)
        },
        "monthly": {
            "total_sales": float(total_month_sales),
            "total_expenses": float(total_month_expenses),
            "net_cash": float(total_month_sales - total_month_expenses),
            "profit": float(total_month_sales - total_month_cost - total_month_expenses)
        },
        "yearly": {
            "total_sales": float(year_sales),
            "total_expenses": float(year_expenses),
            "profit": float(year_sales - year_cost - year_expenses)
        }
    })
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_flexible_report(request):
    user_store = request.user.store
    # Pata tarehe kutoka kwenye simu (kama haipo, tumia leo)
    date_str = request.query_params.get('date')
    target_date = parse_date(date_str) if date_str else timezone.now().date()

    # 1. Orodha ya bidhaa zilizouzwa (Daily List)
    sales = Sale.objects.filter(store=user_store, sale_date__date=target_date)
    
    product_summary = []
    total_sales = 0
    total_cost = 0 # Gharama ya kununulia bidhaa zilizouzwa

    for sale in sales:
        total_sales += sale.total_price
        total_cost += (sale.product.buying_price * sale.quantity)
        product_summary.append({
            "name": sale.product.name,
            "qty": sale.quantity,
            "total": sale.total_price
        })

    # 2. Matumizi ya siku hiyo
    expenses = Expense.objects.filter(store=user_store, date=target_date)
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    expense_list = [{"desc": e.description, "amount": e.amount} for e in expenses]

    # 3. Hesabu ya Faida
    # Faida = (Mapato ya Mauzo - Gharama ya Kununulia) - Matumizi
    gross_profit = total_sales - total_cost
    net_profit = gross_profit - total_expenses

    return Response({
        "date": target_date,
        "product_sales": product_summary,
        "total_sales": total_sales,
        "expense_list": expense_list,
        "total_expenses": total_expenses,
        "net_balance": total_sales - total_expenses, # Pesa iliyopo mkononi
        "actual_profit": net_profit # Faida halisi baada ya kutoa mtaji
    })
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def restock_product(request, pk):
    try:
        product = Product.objects.get(pk=pk, store=request.user.store)
        added_stock = int(request.data.get('added_stock', 0))
        new_buying_price = request.data.get('buying_price')

        if added_stock > 0:
            product.stock += added_stock
            
            # Kama bei ya kununulia imebadilika, ipeleke kwenye bidhaa
            if new_buying_price:
                product.buying_price = float(new_buying_price)
                
            product.save()
            return Response({
                "message": f"Stock imeongezeka! Idadi mpya ni {product.stock}",
                "new_stock": product.stock
            }, status=200)
        
        return Response({"error": "Idadi lazima iwe kubwa kuliko sifuri"}, status=400)
    except Product.DoesNotExist:
        return Response({"error": "Bidhaa haijapatikana"}, status=404)
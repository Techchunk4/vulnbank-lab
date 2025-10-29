from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import connection
from .models import Account, Transaction

def user_login(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # VULNERABILITY: SQL Injection
        with connection.cursor() as cursor:
            query = f"SELECT * FROM auth_user WHERE username='{username}' AND password='{password}'"
            try:
                cursor.execute(query)
            except:
                pass
            
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        error = "Invalid credentials"
    return render(request, 'login.html', {'error': error})

@login_required
def dashboard(request):
    account = Account.objects.get(user=request.user)
    
    # VULNERABILITY: IDOR - account_id from GET parameter
    view_account_id = request.GET.get('account_id', account.id)
    
    try:
        viewed_account = Account.objects.get(id=view_account_id)
    except:
        viewed_account = account
    
    transactions = Transaction.objects.filter(
        from_account=viewed_account
    ).order_by('-timestamp')[:10]
    
    return render(request, 'dashboard.html', {
        'account': viewed_account,
        'transactions': transactions,
        'current_user_account': account
    })

@login_required
def transfer(request):
    account = Account.objects.get(user=request.user)
    message = None
    
    if request.method == 'POST':
        to_account_number = request.POST.get('to_account')
        amount = float(request.POST.get('amount'))
        description = request.POST.get('description', '')
        
        try:
            to_account = Account.objects.get(account_number=to_account_number)
            
            # VULNERABILITY: No CSRF protection, race condition possible
            if account.balance >= amount:
                account.balance -= amount
                to_account.balance += amount
                account.save()
                to_account.save()
                
                Transaction.objects.create(
                    from_account=account,
                    to_account=to_account,
                    amount=amount,
                    description=description
                )
                message = f"Successfully transferred ${amount} to {to_account_number}"
            else:
                message = "Insufficient funds"
        except Account.DoesNotExist:
            message = "Account not found"
    
    return render(request, 'transfer.html', {
        'account': account,
        'message': message
    })

def user_logout(request):
    logout(request)
    return redirect('login')

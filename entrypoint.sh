#!/bin/bash

echo "Waiting for postgres..."
while ! pg_isready -h db -p 5432 > /dev/null 2>&1; do
  sleep 1
done
echo "PostgreSQL started"

python manage.py migrate --noinput
python manage.py shell -c "
from django.contrib.auth.models import User
from banking.models import Account

if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser('admin', 'admin@vulnbank.local', 'admin123')
    Account.objects.create(user=admin, account_number='1000000001', balance=50000.00)

if not User.objects.filter(username='alice').exists():
    alice = User.objects.create_user('alice', 'alice@vulnbank.local', 'password123')
    Account.objects.create(user=alice, account_number='1000000002', balance=1500.00)

if not User.objects.filter(username='bob').exists():
    bob = User.objects.create_user('bob', 'bob@vulnbank.local', 'password123')
    Account.objects.create(user=bob, account_number='1000000003', balance=2500.00)
"

exec "$@"

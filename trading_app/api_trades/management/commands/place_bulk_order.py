import csv
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api_trades.models import Stock, Order


class Command(BaseCommand):
    help = 'Place bulk orders from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **kwargs):
        # absolute filepath from gitpod.
        csv_file_path = '/workspace/DRF-Trading/trading_app/data/bulk_order.csv'
        self.stdout.write(f'CSV File Path: {csv_file_path}\n')
        self.stdout.write(f'Current Directory: {os.getcwd()}\n')

        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR('CSV file does not exist'))
            return

        try:
            with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    user_id = row['user_id']
                    stock_id = row['stock_id']
                    order_type = row['order_type']
                    quantity = int(row['quantity'])

                    try:
                        user = User.objects.get(id=user_id)
                        stock = Stock.objects.get(id=stock_id)

                        if order_type == 'sell' and not self.can_sell(user, stock, quantity):
                            self.stdout.write(
                                self.style.ERROR(
                                    f'User {user_id} does not have enough stock to sell for stock ID {stock_id}'))
                            continue

                        Order.objects.create(user=user, stock=stock, order_type=order_type, quantity=quantity)

                    except User.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'User with ID {user_id} does not exist.'))
                    except Stock.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'Stock with ID {stock_id} does not exist.'))

            self.stdout.write(self.style.SUCCESS('Successfully placed bulk orders'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'The file {csv_file_path} does not exist.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))

    def can_sell(self, user, stock, quantity):
        ''' Check if the user has enough stock to sell '''
        buy_orders = Order.objects.filter(user=user, stock=stock, order_type='buy')
        total_buy_quantity = sum(order.quantity for order in buy_orders)
        return total_buy_quantity >= quantity

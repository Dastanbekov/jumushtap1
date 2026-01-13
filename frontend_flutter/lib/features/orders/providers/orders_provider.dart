import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../../../core/api/api_client.dart';

// Models could be in separate files, but for MVP keeping simple
class Order {
  final int id;
  final String title;
  final String description;
  final String status;
  final double price;
  final String customerName;

  Order({required this.id, required this.title, required this.description, required this.status, required this.price, required this.customerName});

  factory Order.fromJson(Map<String, dynamic> json) {
    return Order(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      status: json['status'],
      price: double.parse(json['price'].toString()),
      customerName: json['customer_name'] ?? 'Unknown',
    );
  }
}

class OrdersNotifier extends StateNotifier<AsyncValue<List<Order>>> {
  final Dio _dio;

  OrdersNotifier(this._dio) : super(const AsyncValue.loading()) {
    fetchOrders();
  }

  Future<void> fetchOrders() async {
    try {
      state = const AsyncValue.loading();
      final response = await _dio.get('/orders/');
      final List data = response.data;
      final orders = data.map((e) => Order.fromJson(e)).toList();
      
      state = AsyncValue.data(orders);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }

  Future<void> createOrder(String title, String description, double price) async {
    try {
      await _dio.post('/orders/', data: {
        'title': title,
        'description': description,
        'price': price,
      });
      fetchOrders(); // Refresh
    } catch (e) {
      // Handle error
      rethrow;
    }
  }
}

final ordersProvider = StateNotifierProvider<OrdersNotifier, AsyncValue<List<Order>>>((ref) {
  final dio = ref.watch(apiClientProvider);
  return OrdersNotifier(dio);
});

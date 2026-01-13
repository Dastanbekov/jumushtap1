import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../../../core/api/api_client.dart';

class Deal {
  final int id;
  final String orderTitle;
  final String status;
  final bool workerConfirmed;
  final bool customerConfirmed;
  final String? confirmedAt;

  Deal({
    required this.id,
    required this.orderTitle,
    required this.status,
    required this.workerConfirmed,
    required this.customerConfirmed,
    this.confirmedAt,
  });

  factory Deal.fromJson(Map<String, dynamic> json) {
    return Deal(
      id: json['id'],
      orderTitle: json['order_title'] ?? 'Job',
      status: json['status'],
      workerConfirmed: json['worker_confirmed'],
      customerConfirmed: json['customer_confirmed'],
      confirmedAt: json['confirmed_at'],
    );
  }
}

class DealsNotifier extends StateNotifier<AsyncValue<List<Deal>>> {
  final Dio _dio;

  DealsNotifier(this._dio) : super(const AsyncValue.loading()) {
    fetchDeals();
  }

  Future<void> fetchDeals() async {
    try {
      state = const AsyncValue.loading();
      final res = await _dio.get('/deals/');
      final List data = res.data;
      state = AsyncValue.data(data.map((e) => Deal.fromJson(e)).toList());
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> confirmWorker(int dealId) async {
    try {
      await _dio.post('/deals/$dealId/confirm-worker/');
      fetchDeals(); // Refresh status
    } catch (e) {
      rethrow;
    }
  }

  Future<void> confirmCustomer(int dealId) async {
    try {
      await _dio.post('/deals/$dealId/confirm-customer/');
      fetchDeals(); // Refresh status
    } catch (e) {
      rethrow;
    }
  }
}

final dealsProvider = StateNotifierProvider<DealsNotifier, AsyncValue<List<Deal>>>((ref) {
  final dio = ref.watch(apiClientProvider);
  return DealsNotifier(dio);
});

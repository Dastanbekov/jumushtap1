import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../../../core/api/api_client.dart';

class ResponseModel {
  final int id;
  final int orderId;
  final String workerName;
  final String status;
  final String text;

  ResponseModel({required this.id, required this.orderId, required this.workerName, required this.status, required this.text});

  factory ResponseModel.fromJson(Map<String, dynamic> json) {
    return ResponseModel(
      id: json['id'],
      orderId: json['order'],
      workerName: json['worker_name'] ?? 'Unknown',
      status: json['status'],
      text: json['text'],
    );
  }
}

class ResponsesNotifier extends StateNotifier<AsyncValue<List<ResponseModel>>> {
  final Dio _dio;
  
  ResponsesNotifier(this._dio) : super(const AsyncValue.loading());

  Future<void> fetchResponses(int orderId) async {
    try {
      state = const AsyncValue.loading();
      final res = await _dio.get('/responses/', queryParameters: {'order': orderId});
      final List data = res.data;
      state = AsyncValue.data(data.map((e) => ResponseModel.fromJson(e)).toList());
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> createResponse(int orderId, String text) async {
    try {
      await _dio.post('/responses/', data: {'order': orderId, 'text': text});
      // Refresh responses (though usually worker can't see own response in list unless we fetch)
      // fetchResponses(orderId); 
    } catch (e) {
      rethrow;
    }
  }

  Future<void> acceptResponse(int responseId) async {
    try {
      await _dio.post('/responses/$responseId/accept/');
      // state should update or UI should pop
    } catch (e) {
      rethrow;
    }
  }
}

final responsesProvider = StateNotifierProvider<ResponsesNotifier, AsyncValue<List<ResponseModel>>>((ref) {
  final dio = ref.watch(apiClientProvider);
  return ResponsesNotifier(dio);
});

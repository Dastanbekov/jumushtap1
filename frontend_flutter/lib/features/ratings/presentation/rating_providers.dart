import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/api/api_client.dart';
import '../data/models/rating_models.dart';

final ratingHistoryProvider = FutureProvider.family<List<RatingHistory>, int>((ref, userId) async {
  final dio = ref.watch(apiClientProvider);
  final response = await dio.get('/ratings/$userId/history/');
  return (response.data as List).map((e) => RatingHistory.fromJson(e)).toList();
});

final ratingConfigProvider = FutureProvider<RatingConfig>((ref) async {
  final dio = ref.watch(apiClientProvider);
  final response = await dio.get('/ratings/config/');
  return RatingConfig.fromJson(response.data);
});

final createReviewProvider = MutationProvider<Review, Map<String, dynamic>>((ref) {
  final dio = ref.watch(apiClientProvider);
  return (data) async {
    final response = await dio.post('/reviews/', data: data);
    return Review.fromJson(response.data);
  };
});

// Helper typedef for mutation
typedef MutationProvider<T, P> = Future<T> Function(P) Function(Ref);

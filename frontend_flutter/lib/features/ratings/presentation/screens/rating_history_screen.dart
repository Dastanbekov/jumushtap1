import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../rating_providers.dart';
import '../widgets/star_rating_widget.dart';
import 'package:intl/intl.dart';

class RatingHistoryScreen extends ConsumerWidget {
  final int userId;

  const RatingHistoryScreen({super.key, required this.userId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final historyAsync = ref.watch(ratingHistoryProvider(userId));

    return Scaffold(
      appBar: AppBar(title: const Text('Rating History')),
      body: historyAsync.when(
        data: (history) => ListView.builder(
          itemCount: history.length,
          itemBuilder: (context, index) {
            final item = history[index];
            final isPositive = item.newRating >= item.oldRating;
            
            return ListTile(
              leading: Icon(
                isPositive ? Icons.trending_up : Icons.trending_down,
                color: isPositive ? Colors.green : Colors.red,
              ),
              title: Row(
                children: [
                   Text('${item.oldRating}'),
                   const Icon(Icons.arrow_right_alt, size: 16),
                   Text(
                     '${item.newRating}',
                     style: const TextStyle(fontWeight: FontWeight.bold),
                   ),
                ],
              ),
              subtitle: Text(item.reason.replaceAll('_', ' ').toUpperCase()),
              trailing: Text(
                DateFormat('MMM d, y').format(item.createdAt),
                style: Theme.of(context).textTheme.bodySmall,
              ),
            );
          },
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }
}

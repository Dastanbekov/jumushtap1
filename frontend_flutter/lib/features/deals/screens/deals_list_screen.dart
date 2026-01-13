import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/deals_provider.dart';

class DealsListScreen extends ConsumerWidget {
  const DealsListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dealsAsync = ref.watch(dealsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('My Active Deals')),
      body: dealsAsync.when(
        data: (deals) {
          if (deals.isEmpty) return const Center(child: Text('No active deals'));
          return ListView.builder(
            itemCount: deals.length,
            itemBuilder: (context, index) {
              final deal = deals[index];
              return Card(
                child: ListTile(
                  title: Text(deal.orderTitle),
                  subtitle: Text('Status: ${deal.status}'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push('/deals/${deal.id}', extra: deal),
                ),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, s) => Center(child: Text('Error: $e')),
      ),
    );
  }
}

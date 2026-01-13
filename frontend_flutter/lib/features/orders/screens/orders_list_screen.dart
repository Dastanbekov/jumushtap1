import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/orders_provider.dart';
import '../../auth/providers/auth_provider.dart';

class OrdersListScreen extends ConsumerWidget {
  const OrdersListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ordersAsync = ref.watch(ordersProvider);
    final user = ref.watch(authProvider).user;
    final isCustomer = user?['role'] == 'customer';

    return Scaffold(
      appBar: AppBar(
        title: Text(isCustomer ? 'My Orders' : 'Available Jobs'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => ref.read(authProvider.notifier).logout(),
          ),
        ],
      ),
      body: ordersAsync.when(
        data: (orders) {
          if (orders.isEmpty) {
            return const Center(child: Text('No orders found.'));
          }
          return ListView.builder(
            itemCount: orders.length,
            itemBuilder: (context, index) {
              final order = orders[index];
              return Card(
                margin: const EdgeInsets.all(8),
                child: ListTile(
                  title: Text(order.title),
                  subtitle: Text('${order.status} - \$${order.price}'),
                  trailing: const Icon(Icons.arrow_forward_ios),
                  onTap: () => context.push('/orders/${order.id}', extra: order),
                ),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
      floatingActionButton: isCustomer
          ? FloatingActionButton(
              onPressed: () => context.push('/create-order'),
              child: const Icon(Icons.add),
            )
          : null,
    );
  }
}

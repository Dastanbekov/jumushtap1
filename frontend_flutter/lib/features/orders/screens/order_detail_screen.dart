import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/orders_provider.dart';
import '../providers/responses_provider.dart';
import '../../auth/providers/auth_provider.dart';

class OrderDetailScreen extends ConsumerStatefulWidget {
  final Order order;
  const OrderDetailScreen({super.key, required this.order});

  @override
  ConsumerState<OrderDetailScreen> createState() => _OrderDetailScreenState();
}

class _OrderDetailScreenState extends ConsumerState<OrderDetailScreen> {
  final _responseController = TextEditingController();

  @override
  void initState() {
    super.initState();
    // Fetch responses if I am customer (and owner) - Logic handled by API mostly, but we trigger fetch
    final user = ref.read(authProvider).user;
    if (user?['role'] == 'customer') {
      Future.microtask(() => ref.read(responsesProvider.notifier).fetchResponses(widget.order.id));
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authProvider).user;
    final isCustomer = user?['role'] == 'customer';
    final responsesAsync = ref.watch(responsesProvider);

    return Scaffold(
      appBar: AppBar(title: Text(widget.order.title)),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Price: \$${widget.order.price}', style: const TextStyle(fontSize: 18, color: Colors.green)),
              const SizedBox(height: 8),
              Text('Status: ${widget.order.status}', style: const TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              Text(widget.order.description),
              const Divider(height: 32),
              
              if (isCustomer && widget.order.status == 'open') ...[
                const Text('Responses:', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                responsesAsync.when(
                  data: (responses) {
                    if (responses.isEmpty) return const Text('No responses yet.');
                    return ListView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: responses.length,
                      itemBuilder: (context, index) {
                        final resp = responses[index];
                        return Card(
                          child: ListTile(
                            title: Text(resp.workerName),
                            subtitle: Text(resp.text),
                            trailing: ElevatedButton(
                              onPressed: () async {
                                final api = ref.read(responsesProvider.notifier);
                                await api.acceptResponse(resp.id);
                                if (context.mounted) {
                                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Response accepted!')));
                                  context.pop(); // Go back to refresh or update state
                                }
                              },
                              child: const Text('Accept'),
                            ),
                          ),
                        );
                      },
                    );
                  },
                  loading: () => const CircularProgressIndicator(),
                  error: (e, s) => Text('Error: $e'),
                )
              ] else if (!isCustomer && widget.order.status == 'open') ...[
                 TextField(
                   controller: _responseController,
                   decoration: const InputDecoration(labelText: 'Why are you a good fit?', border: OutlineInputBorder()),
                   maxLines: 3,
                 ),
                 const SizedBox(height: 16),
                 ElevatedButton(
                   onPressed: () async {
                      try {
                        await ref.read(responsesProvider.notifier).createResponse(widget.order.id, _responseController.text);
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Response sent!')));
                          context.pop();
                        }
                      } catch (e) {
                         if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
                      }
                   },
                   child: const Text('Send Response'),
                 )
              ]
            ],
          ),
        ),
      ),
    );
  }
}

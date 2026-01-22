import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/deals_provider.dart';
import '../../auth/providers/auth_provider.dart';
import 'qr_display_screen.dart';
import 'qr_scan_screen.dart';

class DealDetailScreen extends ConsumerWidget {
  final Deal deal;
  const DealDetailScreen({super.key, required this.deal});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // We might want to watch the specific deal from the list to get updates
    final dealsAsync = ref.watch(dealsProvider);
    final user = ref.watch(authProvider).user;
    final role = user?['role'];

    // Find updated deal object from provider
    final Deal? currentDeal = dealsAsync.value?.firstWhere((d) => d.id == deal.id, orElse: () => deal);
    
    // Fallback if not found
    final d = currentDeal ?? deal;

    return Scaffold(
      appBar: AppBar(title: const Text('Deal Details')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Text('Job: ${d.orderTitle}', style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    Text('Status: ${d.status}', style: const TextStyle(fontWeight: FontWeight.bold)),
                    if (d.startedAt != null)
                      Text('Started: ${d.startedAt}'),
                    if (d.finishedAt != null)
                      Text('Finished: ${d.finishedAt}'),
                    const Divider(),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('Worker Confirmed: ${d.workerConfirmed ? "✅" : "❌"}'),
                        Text('Customer Confirmed: ${d.customerConfirmed ? "✅" : "❌"}'),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),
            
            // QR Check-in Logic
            if (d.status == 'in_progress' || d.status == 'started') ...[
               if (role == 'customer')
                 ElevatedButton.icon(
                   label: const Text('Show QR Code'),
                   icon: const Icon(Icons.qr_code),
                   style: ElevatedButton.styleFrom(minimumSize: const Size.fromHeight(50)),
                   onPressed: () {
                     if (d.qrToken != null) {
                       Navigator.push(context, MaterialPageRoute(
                         builder: (_) => QrDisplayScreen(qrData: d.qrToken!)
                       ));
                     } else {
                       ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('No QR Token available')));
                     }
                   },
                 ),
                 
               if (role == 'worker')
                 ElevatedButton.icon(
                   label: Text(d.status == 'in_progress' ? 'Scan to Start' : 'Scan to Finish'),
                   icon: const Icon(Icons.qr_code_scanner),
                   style: ElevatedButton.styleFrom(minimumSize: const Size.fromHeight(50)),
                   onPressed: () {
                     Navigator.push(context, MaterialPageRoute(
                       builder: (_) => QrScanScreen(onScan: (code) {
                          // Call logic to verify scan
                          // ref.read(dealsProvider.notifier).checkIn(d.id, code);
                          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Scanned: $code')));
                       })
                     ));
                   },
                 ),
            ],

            const Spacer(),
            if (role == 'worker' && !d.workerConfirmed && d.status != 'finished')
              ElevatedButton.icon(
                label: const Text('Confirm Work Done'),
                icon: const Icon(Icons.check),
                style: ElevatedButton.styleFrom(minimumSize: const Size.fromHeight(50)),
                onPressed: () {
                   ref.read(dealsProvider.notifier).confirmWorker(d.id);
                },
              ),
            if (role == 'customer' && !d.customerConfirmed && d.workerConfirmed && d.status != 'finished')
               ElevatedButton.icon(
                label: const Text('Confirm & Pay'),
                icon: const Icon(Icons.payment),
                style: ElevatedButton.styleFrom(minimumSize: const Size.fromHeight(50)),
                onPressed: () {
                   ref.read(dealsProvider.notifier).confirmCustomer(d.id);
                },
              ),
             if (d.status == 'finished')
               const Text('Deal Completed! Contract Generated.', style: TextStyle(color: Colors.green, fontSize: 18)),
             const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}

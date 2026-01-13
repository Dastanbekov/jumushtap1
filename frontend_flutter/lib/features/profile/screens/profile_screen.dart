import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../auth/providers/auth_provider.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    final user = authState.user;

    if (user == null) return const Center(child: CircularProgressIndicator());

    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        actions: [
          IconButton(
            onPressed: () => ref.read(authProvider.notifier).logout(),
            icon: const Icon(Icons.logout),
          )
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
             CircleAvatar(
               radius: 50,
               child: Text(user['username'][0].toUpperCase(), style: const TextStyle(fontSize: 40)),
             ),
             const SizedBox(height: 16),
             Text(user['username'], style: Theme.of(context).textTheme.headlineMedium),
             Text(user['email'] ?? 'No Email', style: Theme.of(context).textTheme.bodyLarge),
             const SizedBox(height: 32),
             Card(
               child: ListTile(
                 title: const Text('Role'),
                 subtitle: Text(user['role'].toString().toUpperCase()),
                 leading: const Icon(Icons.badge),
               ),
             ),
             const SizedBox(height: 8),
             Card(
               child: ListTile(
                 title: const Text('Rating'),
                 subtitle: Text('${user['rating']} / 5.0'),
                 leading: const Icon(Icons.star),
               ),
             ),
             const SizedBox(height: 8),
             Card(
               child: ListTile(
                 title: const Text('Status'),
                 subtitle: Text(user['status']),
                 leading: const Icon(Icons.info),
               ),
             ),
          ],
        ),
      ),
    );
  }
}

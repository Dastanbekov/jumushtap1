import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'dart:async';
import '../../features/auth/providers/auth_provider.dart';
import '../../features/auth/screens/login_screen.dart';
import '../../features/auth/screens/register_screen.dart';
import '../../shared/widgets/main_layout.dart';

// Feature screens
import '../../features/orders/screens/orders_list_screen.dart';
import '../../features/orders/screens/create_order_screen.dart';
import '../../features/orders/screens/order_detail_screen.dart';
import '../../features/orders/providers/orders_provider.dart'; 
import '../../features/deals/screens/deals_list_screen.dart';
import '../../features/deals/screens/deal_detail_screen.dart';
import '../../features/profile/screens/profile_screen.dart';
import '../../features/deals/providers/deals_provider.dart'; // For Deal model

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/',
    refreshListenable: _GoRouterRefreshStream(ref.read(authProvider.notifier).stream),
    redirect: (context, state) {
      final isAuthenticated = authState.isAuthenticated;
      final isLoginRoute = state.uri.path == '/login';
      final isRegisterRoute = state.uri.path == '/register';

      if (!isAuthenticated) {
        return (isLoginRoute || isRegisterRoute) ? null : '/login';
      }

      if (isLoginRoute || isRegisterRoute) {
        return '/';
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/create-order',
        builder: (context, state) => const CreateOrderScreen(),
      ),
      GoRoute(
        path: '/orders/:id',
        builder: (context, state) {
           final order = state.extra as Order; 
           return OrderDetailScreen(order: order);
        }
      ),
      GoRoute(
        path: '/deals/:id',
        builder: (context, state) {
          final deal = state.extra as Deal;
          return DealDetailScreen(deal: deal);
        }
      ),
      ShellRoute(
        builder: (context, state, child) => MainLayout(child: child),
        routes: [
          GoRoute(
            path: '/',
            builder: (context, state) => const OrdersListScreen(),
          ),
          GoRoute(
            path: '/deals',
            builder: (context, state) => const DealsListScreen(),
          ),
          GoRoute(
            path: '/profile',
            builder: (context, state) => const ProfileScreen(),
          ),
        ],
      ),
    ],
  );
});

class _GoRouterRefreshStream extends ChangeNotifier {
  _GoRouterRefreshStream(Stream<AuthState> stream) {
    notifyListeners();
    _subscription = stream.listen((_) => notifyListeners());
  }
  late final StreamSubscription<AuthState> _subscription;

  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }
}

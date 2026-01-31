import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart'; // Импортируем роутер

import 'core/di/service_locator.dart' as di;
import 'core/theme/app_colors.dart'; // Если создал файл с цветами
import 'features/auth/logic/auth_bloc.dart';
import 'features/auth/logic/auth_event.dart';
import 'features/auth/ui/welcome_screen.dart'; // Импорт экрана приветствия
import 'features/auth/ui/role_selection_screen.dart'; // Импорт выбора роли
import 'features/auth/ui/register_customer_screen.dart';
import 'features/auth/ui/register_performer_screen.dart';
import 'features/worker/home/ui/worker_home_screen.dart';
import 'features/customer/home/ui/customer_home_screen.dart';
import 'features/auth/ui/login_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await di.init(); // Инициализация зависимостей
  runApp(const MyApp());
}

// Настройка навигации
final _router = GoRouter(
  initialLocation: '/', // С какого пути начинаем
  routes: [
    // Главный экран (Welcome)
    GoRoute(
      path: '/',
      builder: (context, state) => const WelcomeScreen(),
    ),
    // Экран выбора роли
    GoRoute(
      path: '/role-selection',
      builder: (context, state) => const RoleSelectionScreen(),
    ),
    GoRoute(path: '/register/customer', builder: (context, state) => const RegisterCustomerScreen()),
    GoRoute(path: '/register/performer', builder: (context, state) => const RegisterPerformerScreen()),
    // Главный экран для работника (worker)
    GoRoute(path: '/home', builder: (context, state) => const WorkerHomeScreen()),
    // Главный экран для заказчика (business/individual)
    GoRoute(path: '/customer-home', builder: (context, state) => const CustomerHomeScreen()),
    GoRoute(
      path: '/login',
      builder: (context, state) => const LoginScreen(),
    ),
  ],
);

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      // При запуске сразу проверяем, залогинен ли юзер
      create: (context) => di.sl<AuthBloc>()..add(AuthCheckRequested()),
      
      // Используем MaterialApp.router для поддержки навигации
      child: MaterialApp.router(
        title: 'JumushTap',
        debugShowCheckedModeBanner: false, // Убираем ленточку DEBUG
        
        // Подключаем наш роутер
        routerConfig: _router,

        theme: ThemeData(
          // Ставим оранжевый как основной цвет, чтобы системные элементы (курсоры, ползунки) были в тему
          primaryColor: AppColors.primaryOrange,
          colorScheme: ColorScheme.fromSeed(seedColor: AppColors.primaryOrange),
          useMaterial3: true,
          scaffoldBackgroundColor: Colors.white,
        ),
      ),
    );
  }
}
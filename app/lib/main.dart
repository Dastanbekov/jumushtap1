import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart'; // Импортируем роутер

import 'core/di/service_locator.dart' as di;
import 'core/theme/app_colors.dart'; // Если создал файл с цветами
import 'features/auth/logic/auth_bloc.dart';
import 'features/auth/logic/auth_event.dart';
import 'features/auth/ui/welcome_screen.dart'; // Импорт экрана приветствия
import 'features/auth/ui/role_selection_screen.dart'; // Импорт выбора роли

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
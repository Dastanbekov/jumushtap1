import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/ui/widgets/curved_background.dart';
import '../../../core/ui/widgets/custom_text_field.dart';
import '../logic/auth_bloc.dart';
import '../logic/auth_event.dart';
import '../logic/auth_state.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  // Контроллеры для полей ввода
  final emailController = TextEditingController();
  final passwordController = TextEditingController();

  // Функция нажатия на кнопку "Войти"
  void _onLoginPressed() {
    final email = emailController.text.trim();
    final password = passwordController.text.trim();

    if (email.isEmpty || password.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Заполните все поля")),
      );
      return;
    }

    // Отправляем событие в BLoC
    context.read<AuthBloc>().add(
          AuthLoginRequested(email: email, password: password),
        );
  }

  @override
  Widget build(BuildContext context) {
    // Слушаем изменения состояния (Успех или Ошибка)
    return BlocListener<AuthBloc, AuthState>(
      listener: (context, state) {
        if (state.status == AuthStatus.authenticated) {
          // Если успешно вошли -> идем домой
          context.go('/home');
        } else if (state.status == AuthStatus.error) {
          // Если ошибка -> показываем сообщение
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(state.errorMessage ?? "Ошибка входа"),
              backgroundColor: Colors.red,
            ),
          );
        }
      },
      child: Scaffold(
        backgroundColor: Colors.white,
        body: SingleChildScrollView(
          child: Column(
            children: [
              // 1. Шапка с волной
              SizedBox(
                height: 280, // Высота шапки как на дизайне
                child: Stack(
                  children: [
                    const CurvedBackground(height: 280),
                    
                    // Логотип по центру шапки
                    Center(
                      child: Image.asset(
                        'assets/images/logo_white.png',
                        width: 80,
                        height: 80,
                      ),
                    ),
                    
                    // Кнопка "Назад"
                    Positioned(
                      top: 50,
                      left: 16,
                      child: IconButton(
                        icon: const Icon(Icons.arrow_back_ios, color: Colors.white),
                        onPressed: () => context.pop(), // Возврат назад
                      ),
                    )
                  ],
                ),
              ),

              // 2. Форма входа
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24.0),
                child: Column(
                  children: [
                    const SizedBox(height: 20),
                    
                    // Заголовок "Войти"
                    const Text(
                      "Войти",
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textDark,
                      ),
                    ),
                    const SizedBox(height: 8),
                    
                    // Подзаголовок
                    const Text(
                      "Продолжите работу в Jumush Tap",
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey,
                      ),
                    ),
                    
                    const SizedBox(height: 40),

                    // Поле Email
                    CustomTextField(
                      hintText: "Электронная почта", // или user@gmail.com как в примере
                      icon: Icons.email_outlined,
                      controller: emailController,
                      keyboardType: TextInputType.emailAddress,
                    ),

                    // Поле Пароль
                    CustomTextField(
                      hintText: "Пароль",
                      icon: Icons.lock_outline,
                      controller: passwordController,
                      isPassword: true,
                    ),

                    // Кнопка "Забыли пароль?"
                    Align(
                      alignment: Alignment.centerRight,
                      child: TextButton(
                        onPressed: () {
                          // Пока просто принт, позже можно сделать экран восстановления
                          print("Forgot password tapped");
                        },
                        child: const Text(
                          "Забыли пароль?",
                          style: TextStyle(
                            color: AppColors.primaryTeal, // Цвет морской волны
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ),

                    const SizedBox(height: 30),

                    // Кнопка "ВОЙТИ"
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: _onLoginPressed,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.primaryTeal,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(25),
                          ),
                          elevation: 5,
                          shadowColor: AppColors.primaryTeal.withOpacity(0.4),
                        ),
                        child: const Text(
                          "Войти",
                          style: TextStyle(
                            fontSize: 16,
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),

                    const SizedBox(height: 30),

                    // Текст "Нет аккаунта? Зарегистрироваться"
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Text(
                          "Нет аккаунта? ",
                          style: TextStyle(color: Colors.grey),
                        ),
                        GestureDetector(
                          onTap: () {
                            // Переход на выбор роли
                            context.push('/role-selection');
                          },
                          child: const Text(
                            "Зарегистрироваться",
                            style: TextStyle(
                              color: AppColors.primaryOrange,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                    
                    const SizedBox(height: 40),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
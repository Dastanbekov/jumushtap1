import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/ui/widgets/curved_background.dart';

class RoleSelectionScreen extends StatelessWidget {
  const RoleSelectionScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final screenHeight = MediaQuery.of(context).size.height;

    return Scaffold(
      backgroundColor: Colors.white,
      body: Stack(
        children: [
          // Шапка
          CurvedBackground(
            height: screenHeight * 0.3,
            child: Stack(
              children: [
                Center(
                  child: Image.asset(
                    'assets/images/logo_white.png',
                    width: 70,
                    height: 70,
                  ),
                ),
                Positioned(
                  top: 50,
                  left: 16,
                  child: IconButton(
                    icon: const Icon(Icons.arrow_back_ios, color: Colors.white),
                    onPressed: () => context.pop(),
                  ),
                )
              ],
            ),
          ),

          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24.0),
              child: Column(
                children: [
                  SizedBox(height: screenHeight * 0.25),
                  
                  const Text(
                    "Как вы хотите пользоваться\nприложением?",
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textDark,
                    ),
                  ),

                  const SizedBox(height: 30),

                  // Карточка Заказчика
                  _RoleCard(
                    title: "Заказчик",
                    subtitle: "Размещать смены и\nнаходить исполнителей",
                    color: const Color(0xFFE64A19), 
                    icon: Icons.person,
                    onTap: () {
                      // --- ВОТ ЗДЕСЬ ИЗМЕНЕНИЕ ---
                      // Переходим на экран регистрации ЗАКАЗЧИКА
                      context.push('/register/customer');
                    },
                  ),

                  const SizedBox(height: 20),

                  // Карточка Исполнителя
                  _RoleCard(
                    title: "Исполнитель",
                    subtitle: "Находить работу и выходить\nна смены",
                    color: AppColors.primaryTeal,
                    icon: Icons.work, 
                    onTap: () {
                       // --- И ЗДЕСЬ ИЗМЕНЕНИЕ ---
                       // Переходим на экран регистрации ИСПОЛНИТЕЛЯ
                       context.push('/register/performer');
                    },
                  ),
                ],
              ),
            ),
          )
        ],
      ),
    );
  }
}

// _RoleCard оставляем таким же, он у тебя правильный
class _RoleCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final Color color;
  final IconData icon;
  final VoidCallback onTap;

  const _RoleCard({
    super.key, // Добавил super.key для порядка
    required this.title,
    required this.subtitle,
    required this.color,
    required this.icon,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 100,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(15),
          border: Border.all(color: color, width: 1),
          boxShadow: [
            BoxShadow(
              color: Colors.grey.withOpacity(0.1),
              spreadRadius: 2,
              blurRadius: 5,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              width: 80,
              decoration: BoxDecoration(
                color: color,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(14),
                  bottomLeft: Radius.circular(14),
                ),
              ),
              child: Center(
                child: Icon(icon, color: Colors.white, size: 40),
              ),
            ),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(12.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        color: color,
                        fontWeight: FontWeight.bold,
                        fontSize: 18,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      subtitle,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppColors.textDark,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
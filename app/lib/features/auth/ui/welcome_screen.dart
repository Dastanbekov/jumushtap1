import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/ui/widgets/curved_background.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final screenHeight = MediaQuery.of(context).size.height;

    return Scaffold(
      backgroundColor: Colors.white,
      body: Stack(
        children: [
          // 1. Оранжевая шапка с логотипом
          CurvedBackground(
            height: screenHeight * 0.35, // 35% высоты экрана
            child: Center(
              child: Image.asset(
                'assets/images/logo_white.png', // Логотип J
                width: 80,
                height: 80,
              ),
            ),
          ),

          // 2. Контент
          SafeArea(
            child: Column(
              children: [
                SizedBox(height: screenHeight * 0.30), // Отступ под шапку

                // Заголовок
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 24.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        "Работа и смены рядом\nс вами",
                        style: TextStyle(
                          fontSize: 26,
                          fontWeight: FontWeight.bold,
                          color: AppColors.primaryOrange,
                          height: 1.2,
                        ),
                      ),
                      SizedBox(height: 10),
                      Text(
                        "Выходите на смены уже сегодня!",
                        style: TextStyle(
                          fontSize: 16,
                          color: AppColors.textDark,
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 30),

                // Кнопки
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24.0),
                  child: Row(
                    children: [
                      // Кнопка "Войти"
                      Expanded(
                        child: ElevatedButton(
                          onPressed: () {
                             // Пока просто принт, позже навигация на логин
                             context.push('/login');
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primaryTeal,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(25),
                            ),
                            padding: const EdgeInsets.symmetric(vertical: 14),
                          ),
                          child: const Text(
                            "Войти",
                            style: TextStyle(fontSize: 16, color: Colors.white),
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      // Кнопка "Зарегистрироваться"
                      Expanded(
                        child: ElevatedButton(
                          onPressed: () {
                            // Переход на экран выбора роли
                            context.push('/role-selection');
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primaryOrange,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(25),
                            ),
                            padding: const EdgeInsets.symmetric(vertical: 14),
                          ),
                          child: const Text(
                            "Зарегистрироваться",
                            style: TextStyle(fontSize: 14, color: Colors.white),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                
                // ... верхняя часть кода без изменений (SizedBox, Text, Buttons) ...

                const SizedBox(height: 10),
                const Text(
                  "Бесплатно • Без подписки • По всему Кыргызстану",
                  style: TextStyle(fontSize: 12, color: AppColors.greySubtext),
                ),

                // --- ИЗМЕНЕНИЯ НАЧИНАЮТСЯ ЗДЕСЬ ---
                
                // Вместо Spacer() используем Expanded.
                // Он говорит: "Займи всё доступное место до низа экрана, но не больше"
                Expanded(
                  child: Align(
                    alignment: Alignment.bottomCenter, // Прижимаем картинку к самому низу
                    child: Image.asset(
                       'assets/images/worker_man.png',
                       // width: double.infinity, // Можно убрать, если fit: contain
                       
                       // ВАЖНО: fit.
                       // BoxFit.contain - покажет картинку целиком, чтобы она влезла.
                       // BoxFit.cover - обрежет лишнее, но заполнит ширину (может обрезать голову).
                       // BoxFit.fitWidth - растянет по ширине (может уйти вниз за экран, если высокая).
                       fit: BoxFit.contain, 
                    ),
                  ),
                ),
                
                // --- КОНЕЦ ИЗМЕНЕНИЙ ---
              ],
            ),
          ),
        ],
      ),
    );
  }
}
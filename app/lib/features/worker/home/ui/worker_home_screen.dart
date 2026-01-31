import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import 'widgets/job_card.dart';

/// Главный экран для пользователей типа Worker (Исполнитель)
/// 
/// Отображает ленту доступных вакансий с карточками [JobCard]
class WorkerHomeScreen extends StatefulWidget {
  const WorkerHomeScreen({super.key});

  @override
  State<WorkerHomeScreen> createState() => _WorkerHomeScreenState();
}

class _WorkerHomeScreenState extends State<WorkerHomeScreen> {
  int _selectedIndex = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7F9),
      body: SafeArea(
        child: Column(
          children: [
            // --- HEADER ---
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 10),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  // Аватарка и Имя
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.primaryOrange,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Row(
                      children: [
                        CircleAvatar(
                          radius: 14,
                          backgroundImage: AssetImage('assets/images/worker_man.png'),
                        ),
                        SizedBox(width: 8),
                        Text(
                          "Никита",
                          style: TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        SizedBox(width: 4),
                      ],
                    ),
                  ),

                  // Лого
                  Image.asset(
                    'assets/images/logo_white.png',
                    height: 30,
                    color: AppColors.primaryOrange,
                  ),

                  // Иконки
                  const Row(
                    children: [
                      Icon(Icons.mail_outline, color: AppColors.primaryOrange, size: 28),
                      SizedBox(width: 10),
                      Icon(Icons.notifications_none, color: AppColors.primaryOrange, size: 28),
                    ],
                  )
                ],
              ),
            ),

            // --- СПИСОК ВАКАНСИЙ ---
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                children: const [
                  // Mock карточка
                  JobCard(
                    companyName: 'Супермаркет "Азия"',
                    jobTitle: 'Кассир',
                    location: 'г.Бишкек, 7-мкр',
                    salary: '1 800 сом.',
                    time: '09:00 - 18:00',
                    logoPath: 'assets/images/logo_white.png',
                    tags: ['Сегодня', 'Без опыта'],
                    status: JobStatus.active,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),

      // --- НИЖНЯЯ НАВИГАЦИЯ ---
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(20),
            topRight: Radius.circular(20),
          ),
          boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 10)],
        ),
        child: ClipRRect(
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(20),
            topRight: Radius.circular(20),
          ),
          child: BottomNavigationBar(
            currentIndex: _selectedIndex,
            onTap: (index) => setState(() => _selectedIndex = index),
            selectedItemColor: AppColors.primaryTeal,
            unselectedItemColor: Colors.grey,
            showUnselectedLabels: true,
            items: const [
              BottomNavigationBarItem(icon: Icon(Icons.home), label: "Главная"),
              BottomNavigationBarItem(icon: Icon(Icons.assignment), label: "Мои смены"),
              BottomNavigationBarItem(icon: Icon(Icons.person), label: "Профиль"),
            ],
          ),
        ),
      ),
    );
  }
}

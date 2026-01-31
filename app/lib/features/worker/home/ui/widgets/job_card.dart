import 'package:flutter/material.dart';
import '../../../../../core/theme/app_colors.dart';

/// Статус вакансии - определяет вид кнопки действия
enum JobStatus { active, applied, review, closed }

/// Карточка вакансии для экрана работника
/// 
/// Поддерживает 4 состояния:
/// - [active] - Кнопка "Подробнее"
/// - [applied] - "Вы уже откликнулись"
/// - [review] - "На рассмотрении"
/// - [closed] - "Закрыто"
class JobCard extends StatelessWidget {
  final String companyName;
  final String jobTitle;
  final String location;
  final String salary;
  final String time;
  final String logoPath;
  final List<String> tags;
  final JobStatus status;

  const JobCard({
    super.key,
    required this.companyName,
    required this.jobTitle,
    required this.location,
    required this.salary,
    required this.time,
    required this.logoPath,
    this.tags = const [],
    this.status = JobStatus.active,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.1),
            spreadRadius: 2,
            blurRadius: 8,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. Верхняя строка: Локация и Бейдж даты
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                location,
                style: TextStyle(
                  color: AppColors.primaryOrange.withOpacity(0.8),
                  fontSize: 12,
                ),
              ),
              if (status == JobStatus.active)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.primaryOrange,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Text(
                    "Сегодня",
                    style: TextStyle(color: Colors.white, fontSize: 10),
                  ),
                )
            ],
          ),
          const SizedBox(height: 8),

          // 2. Основная инфа: Название + Лого
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      companyName,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      jobTitle,
                      style: const TextStyle(
                        fontSize: 14,
                        color: AppColors.primaryOrange,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
              // Логотип компании
              Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(10),
                  image: DecorationImage(
                    image: AssetImage(logoPath),
                    fit: BoxFit.contain,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // 3. Зарплата и Время
          Row(
            children: [
              Text(
                salary,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: AppColors.primaryOrange,
                ),
              ),
              const SizedBox(width: 16),
              Text(
                time,
                style: const TextStyle(fontSize: 14, color: Colors.grey),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // 4. Теги и Кнопка
          Row(
            children: [
              ...tags.map((tag) => Container(
                    margin: const EdgeInsets.only(right: 8),
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      border: Border.all(color: AppColors.primaryOrange),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      tag,
                      style: const TextStyle(fontSize: 10, color: Colors.black87),
                    ),
                  )),
              const Spacer(),
              _buildActionButton(),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildActionButton() {
    switch (status) {
      case JobStatus.active:
        return ElevatedButton(
          onPressed: () {},
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.primaryTeal,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(20),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
          ),
          child: const Text(
            "Подробнее",
            style: TextStyle(color: Colors.white, fontSize: 12),
          ),
        );
      case JobStatus.applied:
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: Colors.grey[300],
            borderRadius: BorderRadius.circular(20),
          ),
          child: const Text(
            "Вы уже откликнулись",
            style: TextStyle(color: Colors.grey, fontSize: 12),
          ),
        );
      case JobStatus.review:
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: const Color(0xFFD4A674),
            borderRadius: BorderRadius.circular(20),
          ),
          child: const Text(
            "На рассмотрении",
            style: TextStyle(color: Colors.white, fontSize: 12),
          ),
        );
      case JobStatus.closed:
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: Colors.grey[600],
            borderRadius: BorderRadius.circular(20),
          ),
          child: const Text(
            "Закрыто",
            style: TextStyle(color: Colors.white, fontSize: 12),
          ),
        );
    }
  }
}

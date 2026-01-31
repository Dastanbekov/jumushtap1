import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/ui/widgets/curved_background.dart';
import '../../../core/ui/widgets/custom_text_field.dart';
import '../logic/auth_bloc.dart';
import '../logic/auth_event.dart';
import '../logic/auth_state.dart';

class RegisterCustomerScreen extends StatefulWidget {
  const RegisterCustomerScreen({super.key});

  @override
  State<RegisterCustomerScreen> createState() => _RegisterCustomerScreenState();
}

class _RegisterCustomerScreenState extends State<RegisterCustomerScreen> {
  bool isCompany = true; // Состояние переключателя

  // Контроллеры полей
  final emailCtrl = TextEditingController();
  final passCtrl = TextEditingController();
  final phoneCtrl = TextEditingController();
  
  // Поля компании
  final companyNameCtrl = TextEditingController();
  final binCtrl = TextEditingController();
  final innCtrl = TextEditingController();
  final addressCtrl = TextEditingController();
  final contactNameCtrl = TextEditingController();

  // Поля частника
  final fullNameCtrl = TextEditingController();

  void _onRegister() {
    final Map<String, dynamic> data;

    if (isCompany) {
      // Собираем JSON для Бизнеса
      data = {
        "email": emailCtrl.text,
        "password": passCtrl.text,
        "phone": phoneCtrl.text,
        "user_type": "business",
        "profile": {
          "company_name": companyNameCtrl.text,
          "bin": binCtrl.text,
          "inn": innCtrl.text,
          "legal_address": addressCtrl.text,
          "contact_name": contactNameCtrl.text,
          "contact_number": phoneCtrl.text, 
        }
      };
    } else {
      // Собираем JSON для Частного лица
      data = {
        "email": emailCtrl.text,
        "password": passCtrl.text,
        "phone": phoneCtrl.text,
        "user_type": "individual",
        "profile": {
          "full_name_ru": fullNameCtrl.text,
        }
      };
    }

    // Отправляем событие в Блок
    context.read<AuthBloc>().add(AuthRegisterRequested(data));
  }

  @override
  Widget build(BuildContext context) {
    return BlocListener<AuthBloc, AuthState>(
      listener: (context, state) {
        if (state.status == AuthStatus.authenticated) {
          context.go('/home'); // Успех -> Домой
        } else if (state.status == AuthStatus.error) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(state.errorMessage ?? "Error")));
        }
      },
      child: Scaffold(
        backgroundColor: const Color(0xFFF5F7F9), // Светло-серый фон
        body: SingleChildScrollView(
          child: Column(
            children: [
              // Шапка
              SizedBox(
                height: 180,
                child: Stack(
                  children: [
                    const CurvedBackground(height: 180),
                    Center(child: Image.asset('assets/images/logo_white.png', width: 50)),
                    Positioned(
                       top: 50, left: 10,
                       child: IconButton(icon: const Icon(Icons.arrow_back_ios, color: Colors.white), onPressed: () => context.pop()),
                    ),
                    const Positioned(
                      bottom: 40, left: 0, right: 0,
                      child: Text("Регистрация заказчика", textAlign: TextAlign.center, style: TextStyle(color: Colors.black, fontSize: 18, fontWeight: FontWeight.bold)),
                    )
                  ],
                ),
              ),

              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Column(
                  children: [
                    // Переключатель (Toggle)
                    Container(
                      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(25), border: Border.all(color: Colors.grey.shade300)),
                      child: Row(
                        children: [
                          _ToggleButton(title: "Компания/ИП", isActive: isCompany, onTap: () => setState(() => isCompany = true)),
                          _ToggleButton(title: "Частное лицо", isActive: !isCompany, onTap: () => setState(() => isCompany = false)),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),

                    if (isCompany) ...[
                      CustomTextField(hintText: "Название компании*", icon: Icons.business, controller: companyNameCtrl),
                      Row(
                        children: [
                          Expanded(child: CustomTextField(hintText: "БИН*", icon: Icons.numbers, controller: binCtrl)),
                          const SizedBox(width: 10),
                          Expanded(child: CustomTextField(hintText: "ИНН", icon: Icons.badge, controller: innCtrl)),
                        ],
                      ),
                      CustomTextField(hintText: "Юридический адрес*", icon: Icons.location_on, controller: addressCtrl),
                      CustomTextField(hintText: "Контактное лицо*", icon: Icons.person_pin, controller: contactNameCtrl),
                    ] else ...[
                      CustomTextField(hintText: "ФИО*", icon: Icons.person, controller: fullNameCtrl),
                    ],

                    CustomTextField(hintText: "+996 Phone", icon: Icons.phone, controller: phoneCtrl, keyboardType: TextInputType.phone),
                    CustomTextField(hintText: "Электронная почта*", icon: Icons.email, controller: emailCtrl, keyboardType: TextInputType.emailAddress),
                    CustomTextField(hintText: "Пароль*", icon: Icons.lock, controller: passCtrl, isPassword: true),

                    const SizedBox(height: 20),
                    
                    // Кнопка регистрации
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: _onRegister,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF268C82),
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(25)),
                        ),
                        child: const Text("Зарегистрироваться", style: TextStyle(color: Colors.white, fontSize: 16)),
                      ),
                    ),
                    const SizedBox(height: 40),
                  ],
                ),
              )
            ],
          ),
        ),
      ),
    );
  }
}

// Виджет кнопки переключения
class _ToggleButton extends StatelessWidget {
  final String title;
  final bool isActive;
  final VoidCallback onTap;

  const _ToggleButton({required this.title, required this.isActive, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: isActive ? AppColors.primaryOrange : Colors.transparent,
            borderRadius: BorderRadius.circular(25),
          ),
          child: Text(title, textAlign: TextAlign.center, style: TextStyle(color: isActive ? Colors.white : Colors.black, fontWeight: FontWeight.bold)),
        ),
      ),
    );
  }
}
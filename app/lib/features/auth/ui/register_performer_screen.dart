import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/ui/widgets/curved_background.dart';
import '../../../core/ui/widgets/custom_text_field.dart';
import '../logic/auth_bloc.dart';
import '../logic/auth_event.dart';
import '../logic/auth_state.dart';

class RegisterPerformerScreen extends StatefulWidget {
  const RegisterPerformerScreen({super.key});

  @override
  State<RegisterPerformerScreen> createState() => _RegisterPerformerScreenState();
}

class _RegisterPerformerScreenState extends State<RegisterPerformerScreen> {
  final fullNameCtrl = TextEditingController();
  final phoneCtrl = TextEditingController();
  final emailCtrl = TextEditingController();
  final passCtrl = TextEditingController();

  void _onRegister() {
    final data = {
      "email": emailCtrl.text,
      "password": passCtrl.text,
      "phone": phoneCtrl.text,
      "user_type": "worker",
      "profile": {
        "full_name": fullNameCtrl.text,
      }
    };
    context.read<AuthBloc>().add(AuthRegisterRequested(data));
  }

  @override
  Widget build(BuildContext context) {
    return BlocListener<AuthBloc, AuthState>(
      listener: (context, state) {
        if (state.status == AuthStatus.authenticated) {
          context.go('/home');
        } else if (state.status == AuthStatus.error) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(state.errorMessage ?? "Error")));
        }
      },
      child: Scaffold(
        backgroundColor: const Color(0xFFF5F7F9),
        body: SingleChildScrollView(
          child: Column(
            children: [
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
                      child: Text("Регистрация исполнителя", textAlign: TextAlign.center, style: TextStyle(color: Colors.black, fontSize: 18, fontWeight: FontWeight.bold)),
                    )
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Column(
                  children: [
                    CustomTextField(hintText: "ФИО", icon: Icons.person, controller: fullNameCtrl),
                    CustomTextField(hintText: "+996 Phone", icon: Icons.phone, controller: phoneCtrl, keyboardType: TextInputType.phone),
                    CustomTextField(hintText: "Электронная почта", icon: Icons.email, controller: emailCtrl, keyboardType: TextInputType.emailAddress),
                    CustomTextField(hintText: "Пароль", icon: Icons.lock, controller: passCtrl, isPassword: true),

                    const SizedBox(height: 20),
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
import 'package:equatable/equatable.dart';

abstract class AuthEvent extends Equatable {
  const AuthEvent();

  @override
  List<Object> get props => [];
}

// Событие: Приложение запустилось, нужно проверить токен
class AuthCheckRequested extends AuthEvent {}

// Событие: Пользователь нажал кнопку Логин
class AuthLoginRequested extends AuthEvent {
  final String email;
  final String password;

  const AuthLoginRequested({required this.email, required this.password});

  @override
  List<Object> get props => [email, password];
}
class AuthRegisterRequested extends AuthEvent {
  final Map<String, dynamic> data; // Полный JSON с профилем
  const AuthRegisterRequested(this.data);
  @override
  List<Object> get props => [data];
}
// Событие: Пользователь нажал кнопку Выйти
class AuthLogoutRequested extends AuthEvent {}
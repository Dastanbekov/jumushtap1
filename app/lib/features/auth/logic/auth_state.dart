import 'package:equatable/equatable.dart';

enum AuthStatus { unknown, authenticated, unauthenticated, loading, error }

class AuthState extends Equatable {
  final AuthStatus status;
  final String? errorMessage;
  // Сюда позже можно добавить поле User user; чтобы хранить данные профиля

  const AuthState._({
    this.status = AuthStatus.unknown,
    this.errorMessage,
  });

  // Начальное состояние
  const AuthState.unknown() : this._();

  // Состояние: Загрузка
  const AuthState.loading() : this._(status: AuthStatus.loading);

  // Состояние: Успешный вход
  const AuthState.authenticated() : this._(status: AuthStatus.authenticated);

  // Состояние: Не залогинен (показываем экран логина)
  const AuthState.unauthenticated() : this._(status: AuthStatus.unauthenticated);

  // Состояние: Ошибка
  const AuthState.error(String message) : this._(status: AuthStatus.error, errorMessage: message);

  @override
  List<Object?> get props => [status, errorMessage];
}
import 'package:flutter_bloc/flutter_bloc.dart';
import '../data/auth_repository.dart';
import 'auth_event.dart';
import 'auth_state.dart';

class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final AuthRepository _authRepository;

  AuthBloc(this._authRepository) : super(const AuthState.unknown()) {
    // Регистрируем обработчики событий
    on<AuthCheckRequested>(_onCheckRequested);
    on<AuthLoginRequested>(_onLoginRequested);
    on<AuthLogoutRequested>(_onLogoutRequested);
    on<AuthRegisterRequested>(_onRegisterRequested);
  }
  // В конструкторе добавь:

  // ...

  Future<void> _onRegisterRequested(
    AuthRegisterRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(const AuthState.loading());
    try {
      // Репозиторий сам отправит данные И сохранит токены
      await _authRepository.register(event.data);
      
      // Сразу говорим приложению: "Мы залогинены!"
      emit(const AuthState.authenticated()); 
    } catch (e) {
      emit(AuthState.error(e.toString()));
    }
  }

  // 1. Проверка при старте приложения
  Future<void> _onCheckRequested(
    AuthCheckRequested event,
    Emitter<AuthState> emit,
  ) async {
    try {
      final isLoggedIn = await _authRepository.isLoggedIn();
      if (isLoggedIn) {
        emit(const AuthState.authenticated());
      } else {
        emit(const AuthState.unauthenticated());
      }
    } catch (_) {
      emit(const AuthState.unauthenticated());
    }
  }

  // 2. Логин
  Future<void> _onLoginRequested(
    AuthLoginRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(const AuthState.loading()); // Показываем спиннер

    try {
      await _authRepository.login(event.email, event.password);
      emit(const AuthState.authenticated()); // Успех!
    } catch (e) {
      // e.toString() может быть грязным, лучше брать message из Exception
      // Но для MVP сойдет
      emit(AuthState.error(e.toString().replaceAll('Exception: ', '')));
    }
  }

  // 3. Выход
  Future<void> _onLogoutRequested(
    AuthLogoutRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(const AuthState.loading());
    await _authRepository.logout();
    emit(const AuthState.unauthenticated());
  }
}
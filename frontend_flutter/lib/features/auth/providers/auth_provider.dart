import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:dio/dio.dart';
import '../../../core/api/api_client.dart';

class AuthState {
  final bool isAuthenticated;
  final bool isLoading;
  final String? error;
  final Map<String, dynamic>? user;

  AuthState({
    this.isAuthenticated = false,
    this.isLoading = true,
    this.error,
    this.user,
  });

  AuthState copyWith({
    bool? isAuthenticated,
    bool? isLoading,
    String? error,
    Map<String, dynamic>? user,
  }) {
    return AuthState(
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
      user: user ?? this.user,
    );
  }
}

class AuthNotifier extends StateNotifier<AuthState> {
  final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  AuthNotifier(this._dio) : super(AuthState()) {
    checkAuth();
  }

  Future<void> checkAuth() async {
    final token = await _storage.read(key: 'access_token');
    if (token != null) {
      try {
        final response = await _dio.get('/users/me/');
        state = AuthState(
          isAuthenticated: true,
          isLoading: false,
          user: response.data,
        );
      } catch (e) {
        await logout();
      }
    } else {
      state = state.copyWith(isLoading: false, isAuthenticated: false);
    }
  }

  Future<void> login(String username, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final response = await _dio.post('/auth/login/', data: {
        'username': username,
        'password': password,
      });
      final accessToken = response.data['access'];
      final refreshToken = response.data['refresh'];
      
      await _storage.write(key: 'access_token', value: accessToken);
      await _storage.write(key: 'refresh_token', value: refreshToken);
      
      await checkAuth(); // Load user data
    } on DioException catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.response?.data['detail'] ?? 'Login failed',
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'An unexpected error occurred');
    }
  }

  Future<void> register(String username, String password, String role, String email) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      await _dio.post('/auth/register/', data: {
        'username': username,
        'password': password,
        'role': role,
        'email': email,
      });
      // Auto login after register
      await login(username, password);
    } on DioException catch (e) {
       state = state.copyWith(
        isLoading: false,
        error: e.response?.data.toString() ?? 'Registration failed',
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'Registration error');
    }
  }

  Future<void> logout() async {
    await _storage.deleteAll();
    state = AuthState(isAuthenticated: false, isLoading: false);
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final dio = ref.watch(apiClientProvider);
  return AuthNotifier(dio);
});

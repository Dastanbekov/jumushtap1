import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../../core/network/dio_client.dart';
import 'token_model.dart';

class AuthRepository {
  // Мы используем DioClient, который создали ранее
  final DioClient _dioClient;
  final FlutterSecureStorage _storage;

  AuthRepository(this._dioClient, this._storage);

  // --- ЛОГИН ---
  Future<void> login(String email, String password) async {
    try {
      final response = await _dioClient.dio.post(
        '/auth/login/',
        data: {
          'email': email,
          'password': password,
        },
      );

      // Превращаем JSON в объект
      final tokens = TokenModel.fromJson(response.data);

      // Сохраняем токены в защищенное хранилище
      await _storage.write(key: 'access_token', value: tokens.access);
      await _storage.write(key: 'refresh_token', value: tokens.refresh);
      
    } on DioException catch (e) {
      // Здесь можно обработать ошибку (например, неверный пароль)
      throw Exception(e.response?.data['detail'] ?? 'Login failed');
    }
  }

  // --- РЕГИСТРАЦИЯ ---
  // data — это словарь, который содержит profile и type
 // --- РЕГИСТРАЦИЯ (ОБНОВЛЕННАЯ) ---
  Future<void> register(Map<String, dynamic> registrationData) async {
    try {
      final response = await _dioClient.dio.post(
        '/auth/register/',
        data: registrationData,
      );
      
      // ВАЖНО: Теперь мы ожидаем токены и при регистрации!
      // Превращаем ответ в модель токенов
      final tokens = TokenModel.fromJson(response.data);

      // Сразу сохраняем их, как при логине
      await _storage.write(key: 'access_token', value: tokens.access);
      await _storage.write(key: 'refresh_token', value: tokens.refresh);

    } on DioException catch (e) {
      // Если ошибка (например, такой email уже есть)
      throw Exception(e.response?.data ?? 'Registration failed');
    }
  }
  // --- ПОЛУЧЕНИЕ ПРОФИЛЯ (КТО Я?) ---
  Future<Map<String, dynamic>> getProfile() async {
    try {
      // Достаем токен
      final token = await _storage.read(key: 'access_token');
      
      final response = await _dioClient.dio.get(
        '/auth/me/',
        options: Options(
          headers: {'Authorization': 'Bearer $token'},
        ),
      );
      
      return response.data;
    } catch (e) {
      throw Exception('Failed to load profile');
    }
  }

  // --- ВЫХОД ---
  Future<void> logout() async {
    await _storage.deleteAll();
  }
  
  // Проверка: залогинены ли мы сейчас?
  Future<bool> isLoggedIn() async {
    final token = await _storage.read(key: 'access_token');
    return token != null;
  }
}
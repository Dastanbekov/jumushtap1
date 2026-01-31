import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart'; // <--- Используем это вместо dart:io

class DioClient {
  final Dio _dio;

  DioClient()
      : _dio = Dio(
          BaseOptions(
            baseUrl: _getBaseUrl(), // Вынесли логику в функцию
            connectTimeout: const Duration(seconds: 10),
            receiveTimeout: const Duration(seconds: 10),
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
          ),
        );

  Dio get dio => _dio;

  // Безопасная функция для определения адреса
  static String _getBaseUrl() {
    if (kIsWeb) {
      // Если браузер - всегда localhost
      return 'http://127.0.0.1:8000/api/v1';
    }
    
    // Если Android Эмулятор - спец. адрес 10.0.2.2
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000/api/v1';
    }
    
    // Для iOS симулятора - localhost
    return 'http://127.0.0.1:8000/api/v1';
  }
}
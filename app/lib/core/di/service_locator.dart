// ВАЖНО: Импортируем пакет правильно (package:get_it/get_it.dart)
import 'package:get_it/get_it.dart'; 
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

// Импорты твоих файлов
import '../network/dio_client.dart';
import '../../features/auth/data/auth_repository.dart';
import '../../features/auth/logic/auth_bloc.dart';

final sl = GetIt.instance;

Future<void> init() async {
  // 1. External (Внешние зависимости)
  sl.registerLazySingleton(() => const FlutterSecureStorage());
  sl.registerLazySingleton(() => DioClient());

  // 2. Repositories (Слой данных)
  // AuthRepository требует (DioClient, FlutterSecureStorage)
  sl.registerLazySingleton(() => AuthRepository(sl(), sl()));
  
  // 3. Blocs (Слой логики)
  // AuthBloc требует (AuthRepository)
  sl.registerLazySingleton(() => AuthBloc(sl()));
}
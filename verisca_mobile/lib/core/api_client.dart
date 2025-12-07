import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  late Dio dio;
  final storage = const FlutterSecureStorage();

  // CHANGE THIS TO YOUR LOCAL IP IF RUNNING ON EMULATOR via Network
  // For Windows/Simulator on same machine: http://127.0.0.1:8000
  // For Android Emulator to Localhost: http://10.0.2.2:8000
  // RENDER PRODUCTION URL:
  static const String baseUrl = 'https://verisca.onrender.com';

  factory ApiClient() {
    return _instance;
  }

  ApiClient._internal() {
    dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 60),
      receiveTimeout: const Duration(seconds: 60),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));

    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await storage.read(key: 'access_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (DioException e, handler) {
        // Handle global errors like 401 Unauthorized here
        return handler.next(e);
      },
    ));
  }
}

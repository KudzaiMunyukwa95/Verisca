import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:dio/dio.dart';
import '../../core/api_client.dart';

class AuthProvider extends ChangeNotifier {
  bool _isAuthenticated = false;
  bool _isLoading = false;
  String? _errorMessage;
  final _storage = const FlutterSecureStorage();

  bool get isAuthenticated => _isAuthenticated;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  Future<void> login(String username, String password) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final dio = ApiClient().dio;
      // Using URL encoded form data as per OAuth2 spec usually, but user spec said:
      // Body: username (email), password (JSON? Or Form?) 
      // User Spec: Token Endpoint: POST /api/v1/auth/token Body: username (email), password
      // Usually FastAPI OAuth2PasswordRequestForm expects form-data. 
      // Let's try FormData first as that's standard for /token endpoints in FastAPI.
      
      final response = await dio.post(
        '/api/v1/auth/login',
        data: FormData.fromMap({
          'username': username,
          'password': password,
        }),
        options: Options(contentType: Headers.formUrlEncodedContentType),
      );

      if (response.statusCode == 200) {
        final accessToken = response.data['access_token'];
        await _storage.write(key: 'access_token', value: accessToken);
        _isAuthenticated = true;
      }
    } on DioException catch (e) {
       if (e.response?.statusCode == 401) {
         _errorMessage = "Invalid email or password.";
       } else {
         _errorMessage = "Connection error: ${e.message}";
       }
    } catch (e) {
      _errorMessage = "An unexpected error occurred.";
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await _storage.delete(key: 'access_token');
    _isAuthenticated = false;
    notifyListeners();
  }
    
  Future<void> checkAuthStatus() async {
    final token = await _storage.read(key: 'access_token');
    if (token != null) {
      _isAuthenticated = true;
      notifyListeners();
    }
  }
}

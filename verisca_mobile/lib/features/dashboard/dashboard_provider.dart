import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import '../../core/api_client.dart';
import '../../models/claim.dart';

class DashboardProvider extends ChangeNotifier {
  List<Claim> _claims = [];
  bool _isLoading = false;
  String? _errorMessage;

  List<Claim> get claims => _claims;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  Future<void> fetchAssignments() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final dio = ApiClient().dio;
      // Fetch claims assigned to the current user
      final response = await dio.get('/api/v1/claims/?assigned_to_me=true');

      if (response.statusCode == 200) {
        final List<dynamic> data = response.data;
        _claims = data.map((json) => Claim.fromJson(json)).toList();
      }
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        _errorMessage = "Session expired. Please login again.";
      } else {
        _errorMessage = "Failed to load assignments: ${e.message}";
      }
    } catch (e) {
      _errorMessage = "An unexpected error occurred.";
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}

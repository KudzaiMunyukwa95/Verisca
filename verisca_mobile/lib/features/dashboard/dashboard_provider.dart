import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import '../../core/api_client.dart';
import '../../models/claim.dart';
import '../../services/sync_service.dart';

class DashboardProvider extends ChangeNotifier {
  final SyncService _syncService = SyncService();
  List<Claim> _claims = [];
  bool _isLoading = false;
  String? _errorMessage;

  List<Claim> get claims => _claims;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  // Load claims from local storage (Offline First)
  void loadAssignments() {
    print("Loading Assignments from Local Storage...");
    final offlineData = _syncService.getOfflineClaims();
    print("Found ${offlineData.length} assigned claims offline.");
    
    // cast dynamic list from hive to List<Claim>
    // Assuming Hive stores Map<String, dynamic> or similar
    try {
      _claims = offlineData.map((e) {
        // Handle conversion if Hive returns different type (e.g. Map<dynamic, dynamic>)
        final map = Map<String, dynamic>.from(e as Map);
        return Claim.fromJson(map);
      }).toList();
    } catch (e) {
      print("Error parsing offline claims: $e");
    }
    notifyListeners();
  }

  // Fetch from API and update local storage
  Future<void> fetchAssignments() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      await _syncService.syncDown();
      // Reload from local storage to reflect changes
      loadAssignments();
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        _errorMessage = "Session expired. Please login again.";
      } else {
        // Only show full-screen error if we have no data
        if (_claims.isEmpty) {
          _errorMessage = "Sync failed: ${e.message}";
        } else {
          print("Sync failed (background): ${e.message}");
        }
      }
    } catch (e) {
      if (_claims.isEmpty) {
        _errorMessage = "An unexpected error occurred: $e";
      } else {
        print("Unexpected error (background): $e");
      }
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}

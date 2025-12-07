import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import '../../core/api_client.dart';

class SessionHistoryProvider extends ChangeNotifier {
  bool _isLoading = false;
  String? _errorMessage;
  List<dynamic> _sessions = [];
  
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  List<dynamic> get sessions => _sessions;
  
  // Get most recent completed session
  dynamic get lastCompletedSession {
    try {
      return _sessions.firstWhere(
        (s) => s['status'] == 'completed',
        orElse: () => null
      );
    } catch (e) {
      return null;
    }
  }
  
  // Check if claim has any completed sessions
  bool get hasCompletedSession => lastCompletedSession != null;
  
  // Fetch all sessions for a claim
  Future<void> fetchSessionsForClaim(String claimId) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();
    
    try {
      final dio = ApiClient().dio;
      final response = await dio.get('/api/v1/claims/$claimId/sessions');
      
      if (response.statusCode == 200) {
        _sessions = response.data as List<dynamic>;
      }
    } on DioException catch (e) {
      _errorMessage = "Failed to load sessions: ${e.message}";
      _sessions = [];
    } catch (e) {
      _errorMessage = "Error: $e";
      _sessions = [];
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  // Clear sessions (useful when navigating away)
  void clearSessions() {
    _sessions = [];
    _errorMessage = null;
    notifyListeners();
  }
}

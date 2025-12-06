import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import '../../core/api_client.dart';
import '../../core/location_service.dart';

import '../../models/claim.dart'; // We might need models
import 'dart:convert';

class AssessmentProvider extends ChangeNotifier {
  bool _isLoading = false;
  String? _errorMessage;
  String? _successMessage;
  
  // Assessment State
  String? _currentSessionId;
  List<dynamic> _samples = []; // We"ll define a proper model later or use dynamic for now

  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  String? get successMessage => _successMessage;
  String? get currentSessionId => _currentSessionId;
  List<dynamic> get samples => _samples;

  final LocationService _locationService = LocationService();

  Future<bool> checkIn(String claimId) async {
    _isLoading = true;
    _errorMessage = null;
    _successMessage = null;
    notifyListeners();

    try {
      // 1. Get Location
      final position = await _locationService.getCurrentLocation();

      // 2. Call API
      final dio = ApiClient().dio;
      // Backend expects query params: ?latitude=...&longitude=...
      final response = await dio.post(
        '/api/v1/claims/$claimId/check-in',
        queryParameters: {
          'latitude': position.latitude,
          'longitude': position.longitude,
        },
      );

      if (response.statusCode == 200) {
        final data = response.data;
        _successMessage = data['message'] ?? "Check-in successful!";
        return true;
      }
      return false;

    } on DioException catch (e) {
      if (e.response != null) {
        _errorMessage = e.response?.data['detail'] ?? "Check-in failed.";
      } else {
        _errorMessage = "Connection error: ${e.message}";
      }
      return false;
    } catch (e) {
      _errorMessage = "Error: $e";
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  
  void clearMessages() {
    _errorMessage = null;
    _successMessage = null;
    notifyListeners();
  }

  // --- Assessment Session Logic ---

  Future<bool> startSession(String claimId, String method) async {
    _isLoading = true;
    notifyListeners();
    try {
      final dio = ApiClient().dio;
      final response = await dio.post(
        '/api/v1/claims/$claimId/sessions',
        data: {
          "assessment_method": method,
          "growth_stage": "V5", // Default/Mock for MVP
          "weather_conditions": {"temp": "25C", "condition": "Sunny"},
          "crop_conditions": {"soil": "Moist"},
          "assessor_notes": "Started via Mobile App"
        },
      );

      if (response.statusCode == 201) {
        _currentSessionId = response.data['id'];
        _samples = []; // Reset samples for new session
        return true;
      }
      return false;
    } catch (e) {
      _errorMessage = "Failed to start session: $e";
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> addSample(int sampleNumber, Map<String, dynamic> measurements) async {
    if (_currentSessionId == null) {
      _errorMessage = "No active session";
      notifyListeners();
      return;
    }

    _isLoading = true;
    notifyListeners();

    try {
      final position = await _locationService.getCurrentLocation();
      final dio = ApiClient().dio;
      
      final response = await dio.post(
        '/api/v1/claims/sessions/$_currentSessionId/samples',
        data: {
          "sample_number": sampleNumber,
          "lat": position.latitude,
          "lng": position.longitude,
          "gps_accuracy_meters": position.accuracy,
          "measurements": measurements,
          "notes": "Mobile entry"
        },
      );

      if (response.statusCode == 200) {
        _samples.add(response.data);
        _successMessage = "Sample $sampleNumber saved!";
      }
    } catch (e) {
      _errorMessage = "Failed to save sample: $e";
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}

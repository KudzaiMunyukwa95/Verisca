import 'package:flutter/material.dart';
import 'dart:io';
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
  String? _currentClaimId;
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

  Future<bool> startSession(String claimId, String method, String growthStage) async {
    _isLoading = true;
    notifyListeners();
    try {
      final dio = ApiClient().dio;
      final response = await dio.post(
        '/api/v1/claims/$claimId/sessions',
        data: {
          "claim_id": claimId,
          "assessment_method": method,
          "growth_stage": growthStage,
          "weather_conditions": {"temp": "25C", "condition": "Sunny"},
          "crop_conditions": {"soil": "Moist"},
          "assessor_notes": "Started via Mobile App"
        },
      );

      if (response.statusCode == 201) {
        _currentSessionId = response.data['id'];
        _currentClaimId = claimId;
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

  Future<void> addSample(int sampleNumber, Map<String, dynamic> measurements, [List<String>? evidenceRefs]) async {
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
          "evidence_refs": evidenceRefs ?? [],
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
  Future<String?> uploadEvidence(File imageFile, String description) async {
    if (_currentSessionId == null) {
      _errorMessage = "No active session";
      notifyListeners();
      return null;
    }

    _isLoading = true;
    notifyListeners();

    try {
      final position = await _locationService.getCurrentLocation();
      final dio = ApiClient().dio;
      String fileName = imageFile.path.split(Platform.pathSeparator).last;
      
      FormData formData = FormData.fromMap({
        "file": await MultipartFile.fromFile(imageFile.path, filename: fileName),
        "session_id": _currentSessionId,
        "claim_id": _currentClaimId, 
        "description": description,
        "location_lat": position.latitude,
        "location_lng": position.longitude,
        "gps_accuracy": position.accuracy,
      });

      final response = await dio.post('/api/v1/evidence/upload', data: formData);
      
      if (response.statusCode == 200) {
        _successMessage = "Photo uploaded successfully!";
        return response.data['id']; // Return UUID
      }
      return null;
    } catch (e) {
      _errorMessage = "Upload failed: $e";
      return null;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  Future<Map<String, dynamic>?> completeSession(String growthStage) async {
    if (_currentSessionId == null) return null;
    
    _isLoading = true;
    notifyListeners();

    try {
      final dio = ApiClient().dio;

      // 1. Prepare Calculation Request (Flatten measurements)
      final List<Map<String, dynamic>> flatSamples = _samples.map((s) {
        final m = s['measurements'] as Map<String, dynamic>;
        return {
          "sample_number": s['sample_number'],
          "original_stand_count": m['original_stand_count'],
          "destroyed_plants": m['destroyed_plants'],
          "percent_defoliation": m['percent_defoliation'],
          "stalk_damage_severity": m['stalk_damage_severity'], 
          "growing_point_damage_pct": m['growing_point_damage_pct'],
          "ear_damage_pct": m['ear_damage_pct'],
          "direct_damage_pct": m['direct_damage_pct'],
          "length_measured_m": m['length_measured_m'] ?? 10.0,
          "row_width_m": m['row_width_m'] ?? 0.76,
        };
      }).toList();

      // 2. Call Calculation Engine
      final calcResponse = await dio.post(
        '/api/v1/calculations/hail-damage', 
        data: {
          "growth_stage": growthStage, 
          "normal_plant_population": 40000, 
          "samples": flatSamples
        }
      );

      if (calcResponse.statusCode != 200) {
        throw Exception("Calculation failed");
      }
      
      final result = calcResponse.data;
      
      // 3. Finalize Session
      await dio.patch(
        '/api/v1/claims/$_currentClaimId/sessions/$_currentSessionId',
        data: {
          "status": "completed",
          "calculated_result": result,
          "date_completed": DateTime.now().toIso8601String()
        }
      );
      
      _successMessage = "Assessment Completed!";
      return result;

    } on DioException catch (e) {
      if (e.response != null) {
        _errorMessage = "Server Error: ${e.response?.data}";
      } else {
        _errorMessage = "Network Error: ${e.message}";
      }
      return null;
    } catch (e) {
      _errorMessage = "Completion failed: $e";
      return null;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}

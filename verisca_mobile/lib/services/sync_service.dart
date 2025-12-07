import 'package:hive_flutter/hive_flutter.dart';
import 'package:flutter/foundation.dart';
import '../core/api_client.dart';

class SyncService {
  final ApiClient _apiClient = ApiClient();
  
  Box get _claimsBox => Hive.box('claims');
  Box get _farmsBox => Hive.box('farms');
  Box get _fieldsBox => Hive.box('fields');

  Future<void> syncDown() async {
    try {
      print("Starting Sync Down...");
      // 1. Get last sync time (optional, for now full sync)
      // DateTime? lastSync = ... from prefs;

      // 2. Fetch from API
      // Since ApiClient doesn't have the method yet, we use dio directly for now
      // or we will add the method to ApiClient next.
      final response = await _apiClient.dio.get('/api/v1/sync/down');
      final data = response.data;

      if (data != null) {
        // 3. Store Claims
        if (data['claims'] != null) {
          await _claimsBox.clear(); // Simple strategy: Replace all
          for (var claim in data['claims']) {
            await _claimsBox.put(claim['id'], claim);
          }
        }
        
        // 4. Store Farms
        if (data['farms'] != null) {
          await _farmsBox.clear();
          for (var farm in data['farms']) {
            await _farmsBox.put(farm['id'], farm);
          }
        }
        
        // 5. Store Fields
        if (data['fields'] != null) {
          await _fieldsBox.clear();
          for (var field in data['fields']) {
            await _fieldsBox.put(field['id'], field);
          }
        }
        
        print("Sync Down Complete. Claims: ${_claimsBox.length}");
      }
    } catch (e) {
      print("Sync Down Failed: $e");
      rethrow;
    }
  }

  // Getters for UI
  List<dynamic> getOfflineClaims() {
    return _claimsBox.values.toList();
  }
  
  Map<String, dynamic>? getFarm(String id) {
    return _farmsBox.get(id);
  }
  
  Map<String, dynamic>? getField(String id) {
    return _fieldsBox.get(id);
  }
}

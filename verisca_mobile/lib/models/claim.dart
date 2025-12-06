import 'package:flutter/foundation.dart';

enum ClaimStatus {
  assigned,
  in_progress,
  submitted,
  approved,
  rejected,
  unknown
}

enum PerilType {
  drought,
  hail,
  flood,
  wind,
  disease,
  fire,
  other
}

class ClaimLocation {
  final double lat;
  final double lon;

  ClaimLocation({required this.lat, required this.lon});

  factory ClaimLocation.fromJson(Map<String, dynamic> json) {
    return ClaimLocation(
      lat: (json['lat'] as num).toDouble(),
      lon: (json['lon'] as num).toDouble(),
    );
  }
}

class FarmDetails {
  final String? name; // "farm_name" or just inside details? Spec says "farm_details": { ... }
  // Assuming flexible structure for now based on typical backend responses
  final String? cropType;
  final String? farmName;

  FarmDetails({this.name, this.cropType, this.farmName});

  factory FarmDetails.fromJson(Map<String, dynamic> json) {
    return FarmDetails(
      name: json['name'],
      cropType: json['crop_type'],
      farmName: json['farm_name']
    );
  }
}

class Claim {
  final String id;
  final String claimNumber;
  final ClaimStatus status;
  final PerilType perilType;
  final ClaimLocation? location;
  final FarmDetails? farmDetails;
  final DateTime? dateOfLoss;

  Claim({
    required this.id,
    required this.claimNumber,
    required this.status,
    required this.perilType,
    this.location,
    this.farmDetails,
    this.dateOfLoss,
  });

  factory Claim.fromJson(Map<String, dynamic> json) {
    return Claim(
      id: json['id'],
      claimNumber: json['claim_number'] ?? 'Unknown',
      status: _parseStatus(json['status']),
      perilType: _parsePeril(json['peril_type']),
      location: json['location'] != null ? ClaimLocation.fromJson(json['location']) : null,
      farmDetails: json['farm_details'] != null ? FarmDetails.fromJson(json['farm_details']) : null,
      dateOfLoss: json['date_of_loss'] != null ? DateTime.tryParse(json['date_of_loss']) : null,
    );
  }

  static ClaimStatus _parseStatus(String? status) {
    switch (status?.toLowerCase()) {
      case 'assigned': return ClaimStatus.assigned;
      case 'in_progress': return ClaimStatus.in_progress;
      case 'submitted': return ClaimStatus.submitted;
      default: return ClaimStatus.unknown;
    }
  }

  static PerilType _parsePeril(String? peril) {
    switch (peril?.toLowerCase()) {
      case 'drought': return PerilType.drought;
      case 'hail': return PerilType.hail;
      case 'flood': return PerilType.flood;
      case 'wind': return PerilType.wind;
      case 'disease': return PerilType.disease;
      case 'fire': return PerilType.fire;
      default: return PerilType.other;
    }
  }
}

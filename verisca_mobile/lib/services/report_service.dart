import 'dart:io';
import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../core/api_client.dart';

class ReportService {
  final ApiClient _apiClient = ApiClient();
  
  /// Download PDF report for a claim
  Future<String?> downloadReport(String claimId) async {
    try {
      final dio = _apiClient.dio;
      
      // Get downloads directory
      final directory = await getDownloadsDirectory();
      if (directory == null) {
        throw Exception("Could not access downloads directory");
      }
      
      // Generate filename with timestamp
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final filePath = '${directory.path}/Claim_Report_$timestamp.pdf';
      
      // Download PDF
      final response = await dio.get(
        '/api/v1/claims/$claimId/report',
        options: Options(
          responseType: ResponseType.bytes,
          followRedirects: false,
          validateStatus: (status) => status! < 500,
        ),
      );
      
      if (response.statusCode == 200) {
        // Write to file
        final file = File(filePath);
        await file.writeAsBytes(response.data);
        return filePath;
      } else {
        throw Exception("Failed to download report: ${response.statusCode}");
      }
    } catch (e) {
      print("Error downloading report: $e");
      return null;
    }
  }
  
  /// Open PDF file with system viewer
  Future<bool> openReport(String filePath) async {
    try {
      final uri = Uri.file(filePath);
      if (await canLaunchUrl(uri)) {
        return await launchUrl(uri);
      } else {
        print("Cannot launch URL: $uri");
        return false;
      }
    } catch (e) {
      print("Error opening report: $e");
      return false;
    }
  }
  
  /// Download and open report in one call
  Future<bool> generateAndOpenReport(String claimId) async {
    final filePath = await downloadReport(claimId);
    if (filePath != null) {
      return await openReport(filePath);
    }
    return false;
  }
}

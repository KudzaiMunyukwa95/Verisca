import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/claim.dart';
import '../../features/assessment/assessment_provider.dart';
import '../../features/assessment/assessment_screen.dart';

class ClaimDetailScreen extends StatelessWidget {
  final Claim claim;

  const ClaimDetailScreen({super.key, required this.claim});

  @override
  Widget build(BuildContext context) {
    // Watch provider to show loading state if needed, but usually for button we use Consumer
    return Scaffold(
      appBar: AppBar(
        title: const Text("Claim Details"),
        backgroundColor: const Color(0xFF2E7D32),
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Status Banner
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: _getStatusColor(claim.status).withOpacity(0.1),
                border: Border.all(color: _getStatusColor(claim.status)),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(Icons.info_outline, color: _getStatusColor(claim.status)),
                  const SizedBox(width: 12),
                  Text(
                    claim.status.name.toUpperCase(),
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: _getStatusColor(claim.status),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            _buildSectionHeader("Claim Information"),
            _buildDetailRow("Claim Number", claim.claimNumber),
            _buildDetailRow("Peril Type", claim.perilType.name.toUpperCase()),
            if (claim.dateOfLoss != null)
              _buildDetailRow("Date of Loss", claim.dateOfLoss.toString().split(' ')[0]),

            const SizedBox(height: 24),
            _buildSectionHeader("Location Details"),
            if (claim.farmDetails?.farmName != null)
              _buildDetailRow("Farm Name", claim.farmDetails!.farmName!),
            if (claim.location != null)
               _buildDetailRow("Coordinates", "${claim.location!.lat}, ${claim.location!.lon}"),

            const SizedBox(height: 48),
            
            // Workflow Actions
            Text("Actions", style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 16),
            
            Consumer<AssessmentProvider>(
              builder: (context, provider, child) {
                if (provider.isLoading) {
                  return const Center(child: CircularProgressIndicator());
                }
                
                return SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: () async {
                      final success = await provider.checkIn(claim.id);
                      if (context.mounted) {
                        if (success) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(provider.successMessage ?? "Checked in!"),
                              backgroundColor: Colors.green,
                            ),
                          );
                        } else {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(provider.errorMessage ?? "Check-in failed"),
                              backgroundColor: Colors.red,
                            ),
                          );
                        }
                      }
                    },
                    icon: const Icon(Icons.location_on),
                    label: const Text("ARRIVAL CHECK-IN"),
                    style: FilledButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      backgroundColor: const Color(0xFF2E7D32),
                    ),
                  ),
                );
              },
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () {
                  Navigator.push(
                    context, 
                    MaterialPageRoute(builder: (context) => AssessmentScreen(claim: claim))
                  );
                },
                icon: const Icon(Icons.assignment),
                label: const Text("START / VIEW ASSESSMENT"),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  foregroundColor: const Color(0xFF2E7D32),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getStatusColor(ClaimStatus status) {
    switch (status) {
      case ClaimStatus.assigned: return Colors.orange;
      case ClaimStatus.in_progress: return Colors.blue;
      case ClaimStatus.submitted: return Colors.green;
      default: return Colors.grey;
    }
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: Text(
        title,
        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.black87),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 140,
            child: Text(
              label, 
              style: const TextStyle(
                color: Colors.grey, 
                fontWeight: FontWeight.w500
              )
            ),
          ),
          Expanded(
            child: Text(
              value, 
              style: const TextStyle(
                fontSize: 16, 
                fontWeight: FontWeight.w500
              )
            ),
          ),
        ],
      ),
    );
  }
}

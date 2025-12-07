import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/claim.dart';
import '../../features/assessment/assessment_provider.dart';
import '../../features/assessment/session_history_provider.dart';
import '../../features/assessment/assessment_screen.dart';
import '../../services/report_service.dart';

class ClaimDetailScreen extends StatefulWidget {
  final Claim claim;

  const ClaimDetailScreen({super.key, required this.claim});

  @override
  State<ClaimDetailScreen> createState() => _ClaimDetailScreenState();
}

class _ClaimDetailScreenState extends State<ClaimDetailScreen> {
  @override
  void initState() {
    super.initState();
    // Fetch sessions for this claim on load
    Future.microtask(() =>
        Provider.of<SessionHistoryProvider>(context, listen: false)
            .fetchSessionsForClaim(widget.claim.id));
  }

  @override
  Widget build(BuildContext context) {
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
                color: _getStatusColor(widget.claim.status).withOpacity(0.1),
                border: Border.all(color: _getStatusColor(widget.claim.status)),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(Icons.info_outline, color: _getStatusColor(widget.claim.status)),
                  const SizedBox(width: 12),
                  Text(
                    widget.claim.status.name.toUpperCase(),
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: _getStatusColor(widget.claim.status),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            _buildSectionHeader("Claim Information"),
            _buildDetailRow("Claim Number", widget.claim.claimNumber),
            _buildDetailRow("Peril Type", widget.claim.perilType.name.toUpperCase()),
            if (widget.claim.dateOfLoss != null)
              _buildDetailRow("Date of Loss", widget.claim.dateOfLoss.toString().split(' ')[0]),

            const SizedBox(height: 24),
            _buildSectionHeader("Location Details"),
            if (widget.claim.farmDetails?.farmName != null)
              _buildDetailRow("Farm Name", widget.claim.farmDetails!.farmName!),
            if (widget.claim.location != null)
               _buildDetailRow("Coordinates", "${widget.claim.location!.lat}, ${widget.claim.location!.lon}"),

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
                      final success = await provider.checkIn(widget.claim.id);
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
            
            // Smart Assessment Buttons based on session history
            Consumer<SessionHistoryProvider>(
              builder: (context, sessionProvider, child) {
                if (sessionProvider.isLoading) {
                  return const Center(child: CircularProgressIndicator());
                }
                
                final hasCompleted = sessionProvider.hasCompletedSession;
                final lastSession = sessionProvider.lastCompletedSession;
                
                return Column(
                  children: [
                    // If there's a completed session, show "View Last Assessment" as primary
                    if (hasCompleted) ...[
                      SizedBox(
                        width: double.infinity,
                        child: FilledButton.icon(
                          onPressed: () {
                            _showSessionSummary(context, lastSession);
                          },
                          icon: const Icon(Icons.visibility),
                          label: const Text("VIEW LAST ASSESSMENT"),
                          style: FilledButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 16),
                            backgroundColor: Colors.blue,
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(builder: (context) => AssessmentScreen(claim: widget.claim))
                            );
                          },
                          icon: const Icon(Icons.add),
                          label: const Text("START NEW ASSESSMENT"),
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 16),
                            foregroundColor: const Color(0xFF2E7D32),
                          ),
                        ),
                      ),
                    ] else ...[
                      // No completed session, show single "Start Assessment" button
                      SizedBox(
                        width: double.infinity,
                        child: FilledButton.icon(
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(builder: (context) => AssessmentScreen(claim: widget.claim))
                            );
                          },
                          icon: const Icon(Icons.assignment),
                          label: const Text("START ASSESSMENT"),
                          style: FilledButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 16),
                            backgroundColor: const Color(0xFF2E7D32),
                          ),
                        ),
                      ),
                    ],
                  ],
                );
              },
            ),
            const SizedBox(height: 16),
            
            // Generate Report Button
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () async {
                  // Import ReportService
                  final reportService = ReportService();
                  
                  // Show loading
                  showDialog(
                    context: context,
                    barrierDismissible: false,
                    builder: (context) => const Center(
                      child: CircularProgressIndicator(),
                    ),
                  );
                  
                  // Generate and open report
                  final success = await reportService.generateAndOpenReport(widget.claim.id);
                  
                  // Close loading
                  if (context.mounted) Navigator.pop(context);
                  
                  // Show result
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(success 
                          ? "Report downloaded and opened!" 
                          : "Failed to generate report"),
                        backgroundColor: success ? Colors.green : Colors.red,
                      ),
                    );
                  }
                },
                icon: const Icon(Icons.picture_as_pdf),
                label: const Text("GENERATE PDF REPORT"),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  foregroundColor: Colors.red,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showSessionSummary(BuildContext context, dynamic session) {
    final result = session['calculated_result'];
    final lossPercentage = result?['loss_percentage'] ?? 0.0;
    final yieldPotential = result?['average_potential_yield_pct'] ?? 0.0;
    final sampleCount = (session['samples'] as List?)?.length ?? 0;
    final dateCompleted = session['date_completed'] ?? 'Unknown';
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Assessment Summary"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("Completed: ${dateCompleted.toString().split('T')[0]}"),
            const SizedBox(height: 16),
            Text(
              "Final Loss: ${lossPercentage.toStringAsFixed(2)}%",
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.red),
            ),
            const SizedBox(height: 8),
            Text("Yield Potential: ${yieldPotential.toStringAsFixed(2)}%"),
            const SizedBox(height: 8),
            Text("Samples Collected: $sampleCount"),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("CLOSE"),
          ),
        ],
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

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'assessment_provider.dart';
import '../../models/claim.dart';

class AssessmentScreen extends StatefulWidget {
  final Claim claim;
  const AssessmentScreen({super.key, required this.claim});

  @override
  State<AssessmentScreen> createState() => _AssessmentScreenState();
}

class _AssessmentScreenState extends State<AssessmentScreen> {
  
  @override
  void initState() {
    super.initState();
    // Auto-start session if none exists? 
    // For MVP, we'll try to start one immediately on load if not present.
    // Ideally this should be explicit user action or checked against API.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider = Provider.of<AssessmentProvider>(context, listen: false);
      if (provider.currentSessionId == null) {
        provider.startSession(widget.claim.id, "stand_reduction"); // Default method
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = Provider.of<AssessmentProvider>(context);

    return Scaffold(
      appBar: AppBar(
        title: Text("Assessment: ${widget.claim.perilType.name}"),
        backgroundColor: const Color(0xFF2E7D32),
        foregroundColor: Colors.white,
      ),
      body: provider.isLoading && provider.samples.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                // Session Header
                Container(
                  padding: const EdgeInsets.all(16),
                  color: Colors.green.shade50,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text("Session ID: ...${provider.currentSessionId?.substring(0,6) ?? 'Init...'}"),
                      Chip(label: Text("Samples: ${provider.samples.length}"))
                    ],
                  ),
                ),
                
                // Samples List
                Expanded(
                  child: provider.samples.isEmpty
                      ? const Center(child: Text("No samples collected yet.\nTap + to add one."))
                      : ListView.builder(
                          itemCount: provider.samples.length,
                          itemBuilder: (context, index) {
                            final sample = provider.samples[index];
                            return ListTile(
                              leading: CircleAvatar(child: Text("${sample['sample_number']}")),
                              title: Text("Sample #${sample['sample_number']}"),
                              subtitle: Text("Measurements: ${sample['measurements']}"),
                            );
                          },
                        ),
                ),
              ],
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
            _showAddSampleDialog(context, provider);
        },
        child: const Icon(Icons.add),
      ),
    );
  }

  void _showAddSampleDialog(BuildContext context, AssessmentProvider provider) {
    final _plantCountController = TextEditingController();
    final _gapCountController = TextEditingController();
    
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text("New Sample #${provider.samples.length + 1}"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _plantCountController,
              decoration: const InputDecoration(labelText: "Plant Count (1/1000th ha)"),
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _gapCountController,
              decoration: const InputDecoration(labelText: "Number of Gaps"),
              keyboardType: TextInputType.number,
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
          ElevatedButton(
            onPressed: () {
              final plants = int.tryParse(_plantCountController.text) ?? 0;
              final gaps = int.tryParse(_gapCountController.text) ?? 0;
              
              provider.addSample(
                provider.samples.length + 1,
                {
                  "plant_count": plants,
                  "gap_count": gaps,
                  "row_width_m": 0.76 // Default
                }
              );
              Navigator.pop(ctx);
            },
            child: const Text("Save Sample"),
          ),
        ],
      ),
    );
  }
}

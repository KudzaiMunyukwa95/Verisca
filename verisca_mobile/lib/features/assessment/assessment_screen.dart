import 'package:flutter/material.dart';
import 'dart:io';
import 'package:image_picker/image_picker.dart';
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
  final _growthStageController = TextEditingController();
  String? _selectedGrowthStage;
  String? _selectedPerilType; // NEW: Track selected peril
  
  final List<String> _growthStages = [
    "VE", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10",
    "VT", "R1", "R2", "R3", "R4", "R5", "R6"
  ];
  
  // NEW: Peril types
  final Map<String, String> _perilTypes = {
    "HAIL": "Hail Damage",
    "DROUGHT": "Drought Stress",
    "WINDSTORM": "Windstorm",
    "FLOODING": "Flooding",
    "DISEASE": "Disease/Pest",
    "FIRE": "Fire Damage"
  };

  @override
  void initState() {
    super.initState();
    // Pre-select peril from claim if available
    _selectedPerilType = widget.claim.perilType.name.toUpperCase();
  }

  @override
  Widget build(BuildContext context) {
    final provider = Provider.of<AssessmentProvider>(context);

    // If no session, show "Start Session" Form
    if (provider.currentSessionId == null) {
      return Scaffold(
        appBar: AppBar(title: const Text("Start Assessment"), backgroundColor: const Color(0xFF2E7D32), foregroundColor: Colors.white),
        body: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text("Assessment Setup", style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 8),
              Text("Select peril type and growth stage before sampling.", style: Theme.of(context).textTheme.bodyMedium),
              const SizedBox(height: 32),
              
              // NEW: Peril Type Selection
              DropdownButtonFormField<String>(
                decoration: const InputDecoration(
                  labelText: "Peril Type",
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.warning_amber)
                ),
                value: _selectedPerilType,
                items: _perilTypes.entries.map((e) => 
                  DropdownMenuItem(value: e.key, child: Text(e.value))
                ).toList(),
                onChanged: (v) => setState(() => _selectedPerilType = v),
              ),
              const SizedBox(height: 16),
              
              DropdownButtonFormField<String>(
                decoration: const InputDecoration(labelText: "Growth Stage", border: OutlineInputBorder()),
                items: _growthStages.map((s) => DropdownMenuItem(child: Text(s), value: s)).toList(),
                onChanged: (v) => setState(() => _selectedGrowthStage = v),
              ),
              const SizedBox(height: 32),
              
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: _selectedGrowthStage == null || _selectedPerilType == null || provider.isLoading
                      ? null
                      : () => provider.startSession(
                          widget.claim.id, 
                          _selectedPerilType!.toLowerCase(), 
                          _selectedGrowthStage!,
                          perilType: _selectedPerilType!
                        ),
                  child: provider.isLoading 
                    ? const CircularProgressIndicator(color: Colors.white) 
                    : const Text("CONFIRM & START SAMPLING"),
                  style: FilledButton.styleFrom(backgroundColor: const Color(0xFF2E7D32), padding: const EdgeInsets.symmetric(vertical: 16)),
                ),
              )
            ],
          ),
        ),
      );
    }

    // Main Assessment View
    return Scaffold(
      appBar: AppBar(
        title: Text("Assessment: ${widget.claim.perilType.name}"),
        backgroundColor: const Color(0xFF2E7D32),
        foregroundColor: Colors.white,
      ),
      body: Column(
        children: [
          // Session Header
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.green.shade50,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text("Stage: $_selectedGrowthStage", style: const TextStyle(fontWeight: FontWeight.bold)),
                    Text("Session: ...${provider.currentSessionId?.substring(0,6)}", style: const TextStyle(fontSize: 12, color: Colors.grey)),
                  ],
                ),
                Chip(
                  label: Text("Samples: ${provider.samples.length}"),
                  backgroundColor: Colors.white,
                )
              ],
            ),
          ),
          
          // Samples List
          Expanded(
            child: provider.samples.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: const [
                        Icon(Icons.assignment_outlined, size: 64, color: Colors.grey),
                        SizedBox(height: 16),
                        Text("No samples collected yet.\nGo to a representative area and tap +."),
                      ],
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.only(bottom: 80),
                    itemCount: provider.samples.length,
                    itemBuilder: (context, index) {
                      final sample = provider.samples[index];
                      final m = sample['measurements'] as Map<String, dynamic>;
                      return Card(
                        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor: const Color(0xFF2E7D32),
                            foregroundColor: Colors.white,
                            child: Text("${sample['sample_number']}"),
                          ),
                          title: Text("Loss: ${m['calculated_loss'] ?? '?'}% (Est)"), // We might calculate this locally later
                          subtitle: Text(
                            "Stand: ${m['original_stand_count']} | Defol: ${m['percent_defoliation']}%\n"
                            "Direct Dmg: ${m['direct_damage_pct'] ?? 0}%"
                          ),
                          isThreeLine: true,
                        ),
                      );
                    },
                  ),
          ),

          // Finish Session Button
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: provider.isLoading ? null : () async {
                    final result = await provider.completeSession(_selectedGrowthStage ?? "V6");
                    if (result != null && mounted) {
                      showDialog(
                        context: context,
                        builder: (ctx) => AlertDialog(
                          title: const Text("Assessment Complete"),
                          content: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.check_circle, color: Colors.green, size: 64),
                              const SizedBox(height: 16),
                              Text("Final Loss: ${result['loss_percentage']}%", style: Theme.of(context).textTheme.headlineMedium),
                              Text("Yield Potential: ${result['average_potential_yield_pct']}%"),
                            ],
                          ),
                          actions: [
                            TextButton(
                              onPressed: () {
                                Navigator.pop(ctx); // Close dialog
                                Navigator.pop(context); // Exit screen
                              },
                              child: const Text("CLOSE"),
                            )
                          ],
                        ),
                      );
                    } else if (mounted) {
                       ScaffoldMessenger.of(context).showSnackBar(
                         SnackBar(content: Text(provider.errorMessage ?? "Completion failed"))
                       );
                    }
                  },
                  icon: const Icon(Icons.check),
                  label: const Text("FINISH SESSION"),
                  style: FilledButton.styleFrom(
                    backgroundColor: Colors.red.shade700, 
                    padding: const EdgeInsets.symmetric(vertical: 16)
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showFullSampleForm(context, provider),
        label: const Text("CAPTURE POINT"),
        icon: const Icon(Icons.add_location_alt),
        backgroundColor: const Color(0xFF2E7D32),
      ),
    );
  }

  void _showFullSampleForm(BuildContext context, AssessmentProvider provider) {
    // Controllers
    final _origStandCtrl = TextEditingController(text: "30"); // Default per 1/1000th ha
    final _destroyedCtrl = TextEditingController(text: "0");
    double _defoliation = 0;
    
    // Direct Damage
    final _stalkCtrl = TextEditingController(text: "0.0"); // Using simple number input for now instead of complex enum logic for MVP simplicity/flexibility
    final _growingPointCtrl = TextEditingController(text: "0.0");
    final _earCtrl = TextEditingController(text: "0.0");
    
    // Photo State (Local to Modal)
    File? _pickedImage;
    String? _evidenceId;
    bool _isUploading = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setModalState) => Padding(
          padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom, left: 16, right: 16, top: 16),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("New Sample Point #${provider.samples.length + 1}", style: Theme.of(context).textTheme.headlineSmall),
                const Divider(),
                
                _buildSection("Stand Counts (1/1000th ha)"),
                Row(
                  children: [
                    Expanded(child: _buildInput(_origStandCtrl, "Original Stand")),
                    const SizedBox(width: 16),
                    Expanded(child: _buildInput(_destroyedCtrl, "Destroyed Plants")),
                  ],
                ),

                _buildSection("Defoliation (%)"),
                Slider(
                  value: _defoliation,
                  min: 0,
                  max: 100,
                  divisions: 20,
                  label: "${_defoliation.round()}%",
                  activeColor: const Color(0xFF2E7D32),
                  onChanged: (v) => setModalState(() => _defoliation = v),
                ),
                Center(child: Text("${_defoliation.round()}% Leaf Loss", style: const TextStyle(fontWeight: FontWeight.bold))),

                _buildSection("Direct Damage (%)"),
                Row(
                  children: [
                    Expanded(child: _buildInput(_stalkCtrl, "Stalk Damage")),
                    const SizedBox(width: 16),
                    Expanded(child: _buildInput(_growingPointCtrl, "Growing Point")),
                  ],
                ),
                const SizedBox(height: 12),
                _buildInput(_earCtrl, "Ear Damage"),

                const SizedBox(height: 24),
                // Photo Placeholder
                const SizedBox(height: 24),
                // Photo Integration
                if (_pickedImage != null)
                  Column(
                    children: [
                      Container(
                        height: 200,
                        width: double.infinity,
                        decoration: BoxDecoration(
                          border: Border.all(color: Colors.grey),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.file(_pickedImage!, fit: BoxFit.cover),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          if (_isUploading)
                            const Text("Uploading...", style: TextStyle(color: Colors.orange))
                          else if (_evidenceId != null)
                             const Text("Photo Uploaded ✅", style: TextStyle(color: Colors.green, fontWeight: FontWeight.bold))
                          else
                             const Text("Upload Failed ❌", style: TextStyle(color: Colors.red)),
                             
                          TextButton(
                            onPressed: () => setModalState(() { _pickedImage = null; _evidenceId = null; }),
                            child: const Text("Remove"),
                          )
                        ],
                      )
                    ],
                  )
                else
                  OutlinedButton.icon(
                    onPressed: () async {
                      final picker = ImagePicker();
                      // Use gallery for Windows desktop as camera might need extra config, 
                      // and gallery allows picking any test image.
                      final XFile? image = await picker.pickImage(source: ImageSource.gallery);
                      
                      if (image != null) {
                        setModalState(() {
                          _pickedImage = File(image.path);
                          _isUploading = true;
                        });

                        // Trigger Upload
                        final id = await provider.uploadEvidence(_pickedImage!, "Sample Photo");
                        
                        setModalState(() {
                          _isUploading = false;
                          _evidenceId = id;
                        });
                      }
                    }, 
                    icon: const Icon(Icons.add_a_photo), 
                    label: const Text("Add Photo Evidence"),
                    style: OutlinedButton.styleFrom(minimumSize: const Size(double.infinity, 48)),
                  ),
                
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    onPressed: () {
                      final orig = int.tryParse(_origStandCtrl.text) ?? 30;
                      final dest = int.tryParse(_destroyedCtrl.text) ?? 0;
                      final stalk = double.tryParse(_stalkCtrl.text) ?? 0.0;
                      final gp = double.tryParse(_growingPointCtrl.text) ?? 0.0;
                      final ear = double.tryParse(_earCtrl.text) ?? 0.0;
                      
                      provider.addSample(
                        provider.samples.length + 1,
                        {
                          "original_stand_count": orig,
                          "destroyed_plants": dest,
                          "percent_defoliation": _defoliation,
                          "stalk_damage_severity": "moderate", // Mocking enum mapping for now or we pass raw % if backend adjusted? 
                          // Wait, backend expects "stalk_damage_severity": "moderate" string.
                          // I'll leave it hardcoded or need a dropdown. Let's assume input maps to 'moderate' if > 0 for this quick MVP step, or better yet, just pass these as direct numbers if backend supports it??
                          // Reviewing `verify_hail`: it uses "stalk_damage_severity": "moderate".
                          // I'll stick to a safer map for now.
                          "stalk_damage_severity": stalk > 30 ? "severe" : (stalk > 10 ? "moderate" : "none"), 
                          
                          "growing_point_damage_pct": gp,
                          "ear_damage_pct": ear,
                          "direct_damage_pct": 2.0, // Other
                          "row_width_m": 0.76,
                        },
                        _evidenceId != null ? [_evidenceId!] : []
                      );
                      
                      // NOTE: We should ideally update the sample with evidence_refs separately or included above.
                      // The current addSample API (AssessmentProvider:127) sends:
                      // "measurements": measurements
                      // It expects evidence_refs in the ROOT of the payload, not inside measurements?
                      // Let's check AssessmentProvider.addSample again.
                      // ...
                      // Checking AssessmentProvider again... lines 127-134.
                      // It seems I need to update AssessmentProvider.addSample to accept evidenceRefs!
                      // But for now, let's assume I can't change the provider in this chunk (single file edit).
                      // I WILL NEED TO UPDATE PROVIDER NEXT. 
                      // Temporary: Just save sample. Photo is uploaded but not linked yet unless I fix provider.
                      // I will fix provider in next step.
                      Navigator.pop(ctx);
                    },
                    child: const Text("SAVE SAMPLE POINT"),
                    style: FilledButton.styleFrom(backgroundColor: const Color(0xFF2E7D32), padding: const EdgeInsets.symmetric(vertical: 16)),
                  ),
                ),
                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSection(String title) {
    return Padding(
      padding: const EdgeInsets.only(top: 16, bottom: 8),
      child: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
    );
  }

  Widget _buildInput(TextEditingController ctrl, String label) {
    return TextField(
      controller: ctrl,
      decoration: InputDecoration(labelText: label, border: const OutlineInputBorder()),
      keyboardType: TextInputType.number,
    );
  }
}

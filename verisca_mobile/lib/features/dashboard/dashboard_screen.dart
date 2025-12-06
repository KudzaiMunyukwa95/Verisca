import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'dashboard_provider.dart';
import '../../features/auth/auth_provider.dart';
import '../../models/claim.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    // Fetch data on screen load
    Future.microtask(() =>
        Provider.of<DashboardProvider>(context, listen: false).fetchAssignments());
  }

  @override
  Widget build(BuildContext context) {
    final dashboard = Provider.of<DashboardProvider>(context);
    final auth = Provider.of<AuthProvider>(context, listen: false);

    return Scaffold(
      appBar: AppBar(
        title: const Text("My Assignments"),
        backgroundColor: const Color(0xFF2E7D32),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => dashboard.fetchAssignments(),
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => auth.logout(),
          ),
        ],
      ),
      body: dashboard.isLoading
          ? const Center(child: CircularProgressIndicator())
          : dashboard.errorMessage != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(dashboard.errorMessage!, style: const TextStyle(color: Colors.red)),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () => dashboard.fetchAssignments(),
                        child: const Text("Retry"),
                      )
                    ],
                  ),
                )
              : dashboard.claims.isEmpty
                  ? const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.assignment_turned_in_outlined, size: 64, color: Colors.grey),
                          SizedBox(height: 16),
                          Text("No claims assigned to you yet."),
                        ],
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(8.0),
                      itemCount: dashboard.claims.length,
                      itemBuilder: (context, index) {
                        final claim = dashboard.claims[index];
                        return Card(
                          elevation: 2,
                          margin: const EdgeInsets.symmetric(vertical: 6),
                          child: ListTile(
                            leading: CircleAvatar(
                              backgroundColor: _getPerilColor(claim.perilType),
                              child: Icon(_getPerilIcon(claim.perilType), color: Colors.white),
                            ),
                            title: Text(
                              claim.claimNumber,
                              style: const TextStyle(fontWeight: FontWeight.bold),
                            ),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text("${claim.perilType.name.toUpperCase()} - ${claim.status.name}"),
                                if (claim.farmDetails?.farmName != null)
                                  Text("Farm: ${claim.farmDetails!.farmName}"),
                              ],
                            ),
                            trailing: const Icon(Icons.chevron_right),
                            onTap: () {
                              // TODO: Navigate to Claim Details / Assessment
                            },
                          ),
                        );
                      },
                    ),
    );
  }

  Color _getPerilColor(PerilType type) {
    switch (type) {
      case PerilType.drought: return Colors.orange;
      case PerilType.hail: return Colors.blueGrey;
      case PerilType.flood: return Colors.blue;
      case PerilType.fire: return Colors.red;
      case PerilType.disease: return Colors.purple;
      default: return Colors.green;
    }
  }

  IconData _getPerilIcon(PerilType type) {
    switch (type) {
      case PerilType.drought: return Icons.wb_sunny;
      case PerilType.hail: return Icons.cloud; // best approx
      case PerilType.flood: return Icons.water;
      case PerilType.fire: return Icons.local_fire_department;
      case PerilType.disease: return Icons.coronavirus; // or healing
      default: return Icons.agriculture;
    }
  }
}

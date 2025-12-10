import React, { useContext, useEffect, useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, RefreshControl, ActivityIndicator } from 'react-native';
import { AuthContext } from '../context/AuthContext';
import { getClaims } from '../services/claimsService';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { LogOut, MapPin, Calendar, FileText } from 'lucide-react-native';

const DashboardScreen = ({ navigation }) => {
    const { signOut, user } = useContext(AuthContext);
    const [claims, setClaims] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    const fetchClaims = useCallback(async () => {
        try {
            const data = await getClaims(true);
            setClaims(data);
        } catch (error) {
            // Error is logged in service
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, []);

    useEffect(() => {
        fetchClaims();
    }, [fetchClaims]);

    const onRefresh = useCallback(() => {
        setRefreshing(true);
        fetchClaims();
    }, [fetchClaims]);

    const renderItem = ({ item }) => (
        <TouchableOpacity
            style={styles.card}
            onPress={() => navigation.navigate('ClaimDetail', { claimId: item.id })}
        >
            <View style={styles.cardHeader}>
                <Text style={styles.claimNumber}>{item.claim_number}</Text>
                <View style={[styles.badge, { backgroundColor: getStatusColor(item.status) }]}>
                    <Text style={styles.badgeText}>{item.status}</Text>
                </View>
            </View>

            <View style={styles.cardRow}>
                <Calendar size={16} color="#666" style={styles.icon} />
                <Text style={styles.cardText}>Loss Date: {new Date(item.date_of_loss).toLocaleDateString()}</Text>
            </View>

            <View style={styles.cardRow}>
                <FileText size={16} color="#666" style={styles.icon} />
                <Text style={styles.cardText}>Peril: {item.peril_type}</Text>
            </View>

            <View style={styles.cardRow}>
                <MapPin size={16} color="#666" style={styles.icon} />
                <Text style={styles.cardText} numberOfLines={1}>
                    {item.loss_description || "No description"}
                </Text>
            </View>
        </TouchableOpacity>
    );

    const getStatusColor = (status) => {
        switch (status) {
            case 'REPORTED': return '#3498db'; // Blue
            case 'ASSIGNED': return '#f1c40f'; // Yellow
            case 'IN_PROGRESS': return '#e67e22'; // Orange
            case 'COMPLETED': return '#2ecc71'; // Green
            default: return '#95a5a6'; // Grey
        }
    };

    return (
        <SafeAreaView style={styles.container}>
            <StatusBar style="dark" />
            <View style={styles.header}>
                <View>
                    <Text style={styles.welcomeText}>Hello, {user?.username || 'Assessor'}</Text>
                    <Text style={styles.dateText}>{new Date().toDateString()}</Text>
                </View>
                <TouchableOpacity onPress={signOut} style={styles.logoutButton}>
                    <LogOut size={24} color="#333" />
                </TouchableOpacity>
            </View>

            <Text style={styles.sectionTitle}>My Assignments</Text>

            {loading ? (
                <View style={styles.center}>
                    <ActivityIndicator size="large" color="#007AFF" />
                </View>
            ) : (
                <FlatList
                    data={claims}
                    renderItem={renderItem}
                    keyExtractor={item => item.id}
                    contentContainerStyle={styles.listContent}
                    refreshControl={
                        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
                    }
                    ListEmptyComponent={
                        <View style={styles.center}>
                            <Text style={styles.emptyText}>No claims assigned yet.</Text>
                        </View>
                    }
                />
            )}
        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 20,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#eee',
    },
    welcomeText: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#333',
    },
    dateText: {
        fontSize: 14,
        color: '#666',
        marginTop: 4,
    },
    logoutButton: {
        padding: 8,
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: '600',
        margin: 20,
        marginBottom: 10,
        color: '#333',
    },
    listContent: {
        padding: 16,
    },
    card: {
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 16,
        marginBottom: 16,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.05,
        shadowRadius: 4,
        elevation: 3,
    },
    cardHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 12,
    },
    claimNumber: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#333',
    },
    badge: {
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 12,
    },
    badgeText: {
        color: '#fff',
        fontSize: 12,
        fontWeight: 'bold',
    },
    cardRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 8,
    },
    icon: {
        marginRight: 8,
    },
    cardText: {
        color: '#555',
        fontSize: 14,
        flex: 1,
    },
    center: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 40,
    },
    emptyText: {
        color: '#999',
        fontSize: 16,
    }
});

export default DashboardScreen;

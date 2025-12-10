import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { getClaimDetails, checkIn } from '../services/claimsService';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MapPin, Navigation, AlertTriangle } from 'lucide-react-native';
import * as Location from 'expo-location';

const ClaimDetailScreen = ({ route, navigation }) => {
    const { claimId } = route.params;
    const [claim, setClaim] = useState(null);
    const [loading, setLoading] = useState(true);
    const [checkingIn, setCheckingIn] = useState(false);

    useEffect(() => {
        const loadClaim = async () => {
            try {
                const data = await getClaimDetails(claimId);
                setClaim(data);
            } catch (error) {
                Alert.alert('Error', 'Failed to load claim details');
                navigation.goBack();
            } finally {
                setLoading(false);
            }
        };
        loadClaim();
    }, [claimId]);

    const handleCheckIn = async () => {
        setCheckingIn(true);
        try {
            const { status } = await Location.requestForegroundPermissionsAsync();
            if (status !== 'granted') {
                Alert.alert('Permission to access location was denied');
                return;
            }

            const location = await Location.getCurrentPositionAsync({});
            await checkIn(claimId, location.coords.latitude, location.coords.longitude);

            Alert.alert('Success', 'You have successfully checked in at the field location.');
            // Update claim status locally or refetch
            // Proceed to Assessment
            navigation.navigate('Assessment', { claimId });

        } catch (error) {
            Alert.alert('Check-in Failed', 'Could not verify location. Please try again.');
        } finally {
            setCheckingIn(false);
        }
    };

    if (loading) {
        return (
            <View style={styles.center}>
                <ActivityIndicator size="large" color="#007AFF" />
            </View>
        );
    }

    return (
        <SafeAreaView style={styles.container}>
            <ScrollView contentContainerStyle={styles.content}>
                <View style={styles.headerCard}>
                    <Text style={styles.claimTitle}>{claim?.claim_number}</Text>
                    <Text style={styles.status}>{claim?.status}</Text>
                </View>

                <View style={styles.card}>
                    <Text style={styles.sectionHeader}>Loss Details</Text>
                    <View style={styles.row}>
                        <Text style={styles.label}>Date:</Text>
                        <Text style={styles.value}>{new Date(claim?.date_of_loss).toLocaleDateString()}</Text>
                    </View>
                    <View style={styles.row}>
                        <Text style={styles.label}>Peril:</Text>
                        <Text style={styles.value}>{claim?.peril_type}</Text>
                    </View>
                    <View style={styles.row}>
                        <Text style={styles.label}>Farm ID:</Text>
                        <Text style={styles.value}>{claim?.farm_id}</Text>
                    </View>
                    <View style={styles.row}>
                        <Text style={styles.label}>Description:</Text>
                        <Text style={styles.value}>{claim?.loss_description}</Text>
                    </View>
                </View>

                <View style={styles.actionContainer}>
                    <Text style={styles.instruction}>
                        Arrive at the field location and check-in to start the assessment.
                    </Text>
                    <TouchableOpacity
                        style={styles.checkInButton}
                        onPress={handleCheckIn}
                        disabled={checkingIn}
                    >
                        {checkingIn ? (
                            <ActivityIndicator color="#fff" />
                        ) : (
                            <>
                                <Navigation color="#fff" size={20} style={{ marginRight: 8 }} />
                                <Text style={styles.buttonText}>Check-in & Start Assessment</Text>
                            </>
                        )}
                    </TouchableOpacity>
                </View>
            </ScrollView>
        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    center: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    content: {
        padding: 16,
    },
    headerCard: {
        backgroundColor: '#fff',
        padding: 24,
        borderRadius: 12,
        marginBottom: 16,
        alignItems: 'center',
    },
    claimTitle: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#333',
        marginBottom: 8,
    },
    status: {
        fontSize: 16,
        color: '#007AFF',
        fontWeight: '600',
    },
    card: {
        backgroundColor: '#fff',
        padding: 16,
        borderRadius: 12,
        marginBottom: 24,
    },
    sectionHeader: {
        fontSize: 18,
        fontWeight: '600',
        marginBottom: 16,
        color: '#333',
    },
    row: {
        flexDirection: 'row',
        marginBottom: 12,
    },
    label: {
        width: 100,
        color: '#666',
        fontWeight: '500',
    },
    value: {
        flex: 1,
        color: '#333',
    },
    actionContainer: {
        alignItems: 'center',
    },
    instruction: {
        textAlign: 'center',
        color: '#666',
        marginBottom: 16,
    },
    checkInButton: {
        backgroundColor: '#2ecc71',
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: 16,
        paddingHorizontal: 32,
        borderRadius: 30,
        shadowColor: '#2ecc71',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
        elevation: 5,
    },
    buttonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: 'bold',
    }
});

export default ClaimDetailScreen;

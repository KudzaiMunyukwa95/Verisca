import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, TextInput, Modal, ActivityIndicator, FlatList } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { getSessions, createSession, addSample, uploadEvidence } from '../services/claimsService';
import { calculateStandReduction } from '../services/calculationsService'; // Assuming stand reduction for now
import { Plus, Save, Camera, X } from 'lucide-react-native';
import * as ImagePicker from 'expo-image-picker';
import * as Location from 'expo-location';

const AssessmentScreen = ({ route, navigation }) => {
    const { claimId } = route.params;
    const [session, setSession] = useState(null);
    const [samples, setSamples] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modalVisible, setModalVisible] = useState(false);
    const [liveResult, setLiveResult] = useState(null);

    // New Sample State
    const [plantCount, setPlantCount] = useState('');
    const [gapCount, setGapCount] = useState('');
    const [rowWidth, setRowWidth] = useState('0.76'); // Default meters (30 inch)
    const [lengthMeasured, setLengthMeasured] = useState('5.0'); // Default meters
    const [photo, setPhoto] = useState(null);
    const [submittingSample, setSubmittingSample] = useState(false);

    useEffect(() => {
        loadSession();
    }, []);

    const loadSession = async () => {
        try {
            const sessions = await getSessions(claimId);
            if (sessions && sessions.length > 0) {
                const activeSession = sessions[0]; // Just take first for now, or filter by IN_PROGRESS
                setSession(activeSession);
                setSamples(activeSession.samples || []);
            } else {
                // Create new session
                const newSession = await createSession(claimId, 'stand_reduction');
                setSession(newSession);
                setSamples([]);
            }
        } catch (error) {
            Alert.alert('Error', 'Failed to load assessment session');
        } finally {
            setLoading(false);
        }
    };

    const handleAddSample = async () => {
        if (!plantCount || !gapCount) {
            Alert.alert('Validation', 'Please enter plant and gap counts');
            return;
        }

        setSubmittingSample(true);
        try {
            let evidenceRefs = [];
            // Upload photo if exists
            if (photo) {
                const formData = new FormData();
                formData.append('file', {
                    uri: photo.uri,
                    name: 'sample_photo.jpg',
                    type: 'image/jpeg',
                });
                formData.append('session_id', session.id);
                const uploadRes = await uploadEvidence(formData);
                evidenceRefs.push(uploadRes.id);
            }

            // Get Location
            let lat = 0, lng = 0, acc = 0;
            try {
                const loc = await Location.getCurrentPositionAsync({});
                lat = loc.coords.latitude;
                lng = loc.coords.longitude;
                acc = loc.coords.accuracy;
            } catch (e) {
                console.log("No location");
            }

            const sampleData = {
                sample_number: samples.length + 1,
                lat: lat,
                lng: lng,
                gps_accuracy_meters: acc,
                measurements: {
                    plant_count: parseInt(plantCount),
                    gap_count: parseInt(gapCount),
                    row_width: parseFloat(rowWidth),
                    length_measured: parseFloat(lengthMeasured)
                },
                evidence_refs: evidenceRefs,
                notes: ''
            };

            const newSample = await addSample(session.id, sampleData);
            const updatedSamples = [newSample, ...samples]; // Prepend
            setSamples(updatedSamples);

            // Recalculate Logic (Client Side Trigger)
            // Transform samples for calculation service which expects certain keys
            // Service expects: { plant_count: X, ... } in measurements or root?
            // backend/schemas/calculations.py says SampleInput matches dict structure.
            // Actually the backend `CalculationRequest` expects `samples`: List[SampleInput]
            // SampleInput has `measurements`.

            // Wait, `calculations.py` line 51: `sample_dicts = [sample.model_dump() for sample in request.samples]`
            // `CalculationRequest` has `samples` list.
            // `CalculationService` logic usually extracts measurements.

            // Let's format for Calculation API:
            const calcSamples = updatedSamples.map(s => ({
                ...s,
                measurements: s.measurements // backend service will use measurements
            }));

            const result = await calculateStandReduction(calcSamples);
            setLiveResult(result);

            setModalVisible(false);
            resetForm();

        } catch (error) {
            Alert.alert('Error', 'Failed to save sample');
        } finally {
            setSubmittingSample(false);
        }
    };

    const pickImage = async () => {
        let result = await ImagePicker.launchCameraAsync({
            mediaTypes: ImagePicker.MediaTypeOptions.Images,
            allowsEditing: true,
            quality: 0.5,
        });

        if (!result.canceled) {
            setPhoto(result.assets[0]);
        }
    };

    const resetForm = () => {
        setPlantCount('');
        setGapCount('');
        setPhoto(null);
    };

    const renderSample = ({ item }) => (
        <View style={styles.sampleCard}>
            <Text style={styles.sampleTitle}>Sample #{item.sample_number}</Text>
            <Text>Plants: {item.measurements.plant_count} | Gaps: {item.measurements.gap_count}</Text>
            {item.notes ? <Text style={styles.notes}>{item.notes}</Text> : null}
        </View>
    );

    if (loading) return <ActivityIndicator style={styles.center} size="large" />;

    return (
        <SafeAreaView style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.headerTitle}>Stand Reduction Assessment</Text>
                {liveResult && (
                    <View style={styles.resultBadge}>
                        <Text style={styles.resultText}>Loss: {liveResult.loss_percentage?.toFixed(1)}%</Text>
                    </View>
                )}
            </View>

            <FlatList
                data={samples}
                renderItem={renderSample}
                keyExtractor={item => item.id}
                contentContainerStyle={styles.list}
                ListEmptyComponent={<Text style={styles.empty}>No samples collected yet.</Text>}
            />

            <TouchableOpacity style={styles.fab} onPress={() => setModalVisible(true)}>
                <Plus color="#fff" size={24} />
            </TouchableOpacity>

            <Modal visible={modalVisible} animationType="slide" presentationStyle="pageSheet">
                <View style={styles.modalContainer}>
                    <View style={styles.modalHeader}>
                        <Text style={styles.modalTitle}>New Sample</Text>
                        <TouchableOpacity onPress={() => setModalVisible(false)}>
                            <X size={24} color="#333" />
                        </TouchableOpacity>
                    </View>

                    <ScrollView style={styles.form}>
                        <Text style={styles.label}>Plant Count (in 5m)</Text>
                        <TextInput
                            style={styles.input}
                            keyboardType="numeric"
                            value={plantCount}
                            onChangeText={setPlantCount}
                            placeholder="e.g. 28"
                        />

                        <Text style={styles.label}>Gap Count</Text>
                        <TextInput
                            style={styles.input}
                            keyboardType="numeric"
                            value={gapCount}
                            onChangeText={setGapCount}
                            placeholder="e.g. 2"
                        />

                        <TouchableOpacity style={styles.photoButton} onPress={pickImage}>
                            <Camera size={20} color="#007AFF" style={{ marginRight: 8 }} />
                            <Text style={{ color: '#007AFF' }}>{photo ? 'Retake Photo' : 'Take Photo'}</Text>
                        </TouchableOpacity>
                        {photo && <Text style={{ marginBottom: 16 }}>Photo attached</Text>}

                        <TouchableOpacity
                            style={styles.saveButton}
                            onPress={handleAddSample}
                            disabled={submittingSample}
                        >
                            {submittingSample ? <ActivityIndicator color="#fff" /> : <Text style={styles.saveText}>Save Sample</Text>}
                        </TouchableOpacity>
                    </ScrollView>
                </View>
            </Modal>

        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f5f5f5' },
    center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    header: { padding: 16, backgroundColor: '#fff', flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', borderBottomWidth: 1, borderBottomColor: '#eee' },
    headerTitle: { fontSize: 18, fontWeight: 'bold' },
    resultBadge: { backgroundColor: '#e74c3c', padding: 6, borderRadius: 8 },
    resultText: { color: '#fff', fontWeight: 'bold' },
    list: { padding: 16 },
    empty: { textAlign: 'center', color: '#999', marginTop: 40 },
    sampleCard: { backgroundColor: '#fff', padding: 16, borderRadius: 8, marginBottom: 12 },
    sampleTitle: { fontWeight: 'bold', marginBottom: 4 },
    fab: { position: 'absolute', bottom: 32, right: 32, backgroundColor: '#007AFF', width: 56, height: 56, borderRadius: 28, justifyContent: 'center', alignItems: 'center', elevation: 5, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.3, shadowRadius: 4 },
    modalContainer: { flex: 1, backgroundColor: '#fff', paddingTop: 20 },
    modalHeader: { flexDirection: 'row', justifyContent: 'space-between', padding: 20, alignItems: 'center' },
    modalTitle: { fontSize: 20, fontWeight: 'bold' },
    form: { padding: 20 },
    label: { fontSize: 14, color: '#666', marginBottom: 8, marginTop: 16 },
    input: { borderWidth: 1, borderColor: '#ddd', borderRadius: 8, padding: 12, fontSize: 16, backgroundColor: '#fafafa' },
    photoButton: { flexDirection: 'row', alignItems: 'center', marginTop: 24, marginBottom: 8 },
    saveButton: { backgroundColor: '#007AFF', padding: 16, borderRadius: 8, alignItems: 'center', marginTop: 32 },
    saveText: { color: '#fff', fontWeight: 'bold', fontSize: 16 }
});

export default AssessmentScreen;

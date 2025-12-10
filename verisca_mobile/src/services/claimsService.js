import api from './api';

export const getClaims = async (assignedToMe = true) => {
    try {
        const response = await api.get('/claims/', {
            params: { assigned_to_me: assignedToMe }
        });
        return response.data;
    } catch (error) {
        console.error("Error fetching claims:", error);
        throw error;
    }
};

export const getClaimDetails = async (claimId) => {
    try {
        const response = await api.get(`/claims/${claimId}`);
        return response.data;
    } catch (error) {
        console.error(`Error fetching claim ${claimId}:`, error);
        throw error;
    }
};

export const checkIn = async (claimId, latitude, longitude) => {
    try {
        const response = await api.post(`/claims/${claimId}/check-in`, null, {
            params: { latitude, longitude }
        });
        return response.data;
    } catch (error) {
        console.error("Error check-in:", error);
        throw error;
    }
};

export const createSession = async (claimId, method = 'stand_reduction') => {
    try {
        const response = await api.post(`/claims/${claimId}/sessions`, {
            assessment_method: method,
            growth_stage: 'V1', // Default, should be user input
            weather_conditions: {},
            crop_conditions: {},
            assessor_notes: ''
        });
        return response.data;
    } catch (error) {
        console.error("Error creating session:", error);
        throw error;
    }
};

export const getSessions = async (claimId) => {
    try {
        const response = await api.get(`/claims/${claimId}/sessions`);
        return response.data;
    } catch (error) {
        console.error("Error getting sessions:", error);
        throw error;
    }
};

export const addSample = async (sessionId, sampleData) => {
    try {
        const response = await api.post(`/claims/sessions/${sessionId}/samples`, sampleData);
        return response.data;
    } catch (error) {
        console.error("Error adding sample:", error);
        throw error;
    }
};

export const uploadEvidence = async (formData) => {
    try {
        const response = await api.post('/evidence/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    } catch (error) {
        console.error("Error uploading evidence:", error);
        throw error;
    }
};

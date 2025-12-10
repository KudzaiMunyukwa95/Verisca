import api from './api';

export const calculateStandReduction = async (samples, growthStage = 'V5', normalPopulation = 60000) => {
    try {
        const response = await api.post('/calculations/stand-reduction', {
            samples,
            growth_stage: growthStage,
            normal_plant_population: normalPopulation
        });
        return response.data;
    } catch (error) {
        console.error("Calculation Error:", error);
        throw error;
    }
};

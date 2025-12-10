import api from './api';
import * as SecureStore from 'expo-secure-store';

export const login = async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    // Note: axios serializes FormData automatically if not set to JSON,
    // but for OAuth2PasswordRequestForm it expects form-data.
    // We might need to handle content-type explicitly if axios struggles,
    // but usually passing FormData works.

    // However, React Native's FormData behaves slightly differently.
    // Let's try sending as URL encoded form data if simple FormData fails,
    // but standard OAuth2 expects application/x-www-form-urlencoded often.
    // FastAPI's OAuth2PasswordRequestForm expects form data.

    // For safety with simple OAuth2 forms:
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    const response = await api.post('/auth/login', params.toString(), {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    });

    if (response.data.access_token) {
        await SecureStore.setItemAsync('userToken', response.data.access_token);
        await SecureStore.setItemAsync('userData', JSON.stringify(response.data.user));
    }

    return response.data;
};

export const logout = async () => {
    await SecureStore.deleteItemAsync('userToken');
    await SecureStore.deleteItemAsync('userData');
};

export const getToken = async () => {
    return await SecureStore.getItemAsync('userToken');
};

export const getUser = async () => {
    const user = await SecureStore.getItemAsync('userData');
    return user ? JSON.parse(user) : null;
}

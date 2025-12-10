import React, { createContext, useState, useEffect, useMemo } from 'react';
import { getToken, getUser, login as loginService, logout as logoutService } from '../services/authService';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [userToken, setUserToken] = useState(null);
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const bootstrapAsync = async () => {
            let token;
            let userData;
            try {
                token = await getToken();
                userData = await getUser();
            } catch (e) {
                console.log('Restoring token failed');
            }
            setUserToken(token);
            setUser(userData);
            setIsLoading(false);
        };

        bootstrapAsync();
    }, []);

    const authContext = useMemo(
        () => ({
            signIn: async (username, password) => {
                setIsLoading(true);
                try {
                    const data = await loginService(username, password);
                    setUserToken(data.access_token);
                    setUser(data.user);
                } catch (error) {
                    console.error(error);
                    throw error;
                } finally {
                    setIsLoading(false);
                }
            },
            signOut: async () => {
                setIsLoading(true);
                try {
                    await logoutService();
                    setUserToken(null);
                    setUser(null);
                } catch (e) {
                    console.error(e);
                } finally {
                    setIsLoading(false);
                }
            },
            userToken,
            user,
            isLoading,
        }),
        [userToken, user, isLoading]
    );

    return (
        <AuthContext.Provider value={authContext}>
            {children}
        </AuthContext.Provider>
    );
};

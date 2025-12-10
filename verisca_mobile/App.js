import React, { useContext } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { AuthContext, AuthProvider } from './src/context/AuthContext';
import LoginScreen from './src/screens/LoginScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import { SafeAreaProvider } from 'react-native-safe-area-context';

const Stack = createNativeStackNavigator();

const AppNav = () => {
  const { userToken, isLoading } = useContext(AuthContext);

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator>
        {userToken == null ? (
          // No token found, user isn't signed in
          <Stack.Screen
            name="Login"
            component={LoginScreen}
            options={{ headerShown: false }}
          />
        ) : (
          // User is signed in
          <>
            <Stack.Screen
              name="Dashboard"
              component={DashboardScreen}
              options={{ title: 'Verisca Dashboard' }}
            />
            <Stack.Screen
              name="ClaimDetail"
              component={require('./src/screens/ClaimDetailScreen').default}
              options={{ title: 'Claim Details' }}
            />
            <Stack.Screen
              name="Assessment"
              component={require('./src/screens/AssessmentScreen').default}
              options={{ title: 'Assessment' }}
            />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default function App() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <AppNav />
      </AuthProvider>
    </SafeAreaProvider>
  );
}

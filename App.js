// App.js
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View } from 'react-native';
import Constants from 'expo-constants';

export default function App() {
  const cfg = Constants?.expoConfig ?? {};
  const name = cfg.name ?? 'Unknown';
  const version = cfg.version ?? '0.0.0';
  const androidPkg = cfg.android?.package ?? '(missing)';
  const projectId = cfg.extra?.eas?.projectId ?? '(missing)';

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{name}</Text>
      <Text>Version: {version}</Text>
      <Text>Android package: {androidPkg}</Text>
      <Text>EAS projectId: {projectId}</Text>
      <Text style={{ marginTop: 16 }}>
        If these match your app.json / app.config.js and Expo dashboard,
        the JS side is wired up correctly.
      </Text>
      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff', alignItems: 'center', justifyContent: 'center', padding: 20 },
  title: { fontSize: 20, fontWeight: '600', marginBottom: 8 },
});

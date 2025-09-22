import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { router, useLocalSearchParams } from 'expo-router';

export default function DreamDetailScreen() {
  const { id } = useLocalSearchParams();
  const [dream, setDream] = useState<any>(null);

  useEffect(() => {
    // Mock dream data for now
    const mockDream = {
      id: id,
      title: 'Flying Dream',
      content: 'I was soaring through clouds above my hometown, feeling completely free and weightless. The landscape below looked like a miniature model, and I could control my flight with just my thoughts.',
      created_at: '2025-01-15',
      mood: 'excited',
      is_lucid: true,
    };
    setDream(mockDream);
  }, [id]);

  const handleGenerateAI = (type: string) => {
    Alert.alert(
      'AI Generation',
      `${type} generation feature coming soon! This will connect to your production backend.`,
      [{ text: 'Got it!' }]
    );
  };

  if (!dream) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Text>Loading dream...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <LinearGradient
        colors={['#4338ca', '#7c3aed']}
        style={styles.header}
      >
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={24} color="white" />
        </TouchableOpacity>
        
        <Text style={styles.headerTitle}>{dream.title}</Text>
        <Text style={styles.headerSubtitle}>{dream.created_at}</Text>
      </LinearGradient>

      <ScrollView style={styles.content}>
        {/* Dream Content */}
        <View style={styles.dreamSection}>
          <Text style={styles.dreamContent}>{dream.content}</Text>
          
          {dream.is_lucid && (
            <View style={styles.lucidBadge}>
              <Ionicons name="star" size={16} color="#fbbf24" />
              <Text style={styles.lucidText}>Lucid Dream</Text>
            </View>
          )}
        </View>

        {/* AI Generation Section */}
        <View style={styles.aiSection}>
          <Text style={styles.sectionTitle}>AI Creations</Text>
          
          <TouchableOpacity
            style={styles.aiButton}
            onPress={() => handleGenerateAI('Image')}
          >
            <Ionicons name="image" size={20} color="#7c3aed" />
            <Text style={styles.aiButtonText}>Generate AI Image</Text>
            <Ionicons name="chevron-forward" size={20} color="#7c3aed" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.aiButton}
            onPress={() => handleGenerateAI('Video')}
          >
            <Ionicons name="videocam" size={20} color="#7c3aed" />
            <Text style={styles.aiButtonText}>Generate AI Video</Text>
            <Ionicons name="chevron-forward" size={20} color="#7c3aed" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.aiButton}
            onPress={() => handleGenerateAI('Lucy AI')}
          >
            <Ionicons name="sparkles" size={20} color="#fbbf24" />
            <Text style={styles.aiButtonText}>Ask Lucy AI</Text>
            <View style={styles.premiumBadge}>
              <Text style={styles.premiumText}>Premium</Text>
            </View>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    padding: 24,
    paddingTop: 16,
  },
  backButton: {
    position: 'absolute',
    top: 16,
    left: 24,
    zIndex: 1,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    textAlign: 'center',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  dreamSection: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
  },
  dreamContent: {
    fontSize: 16,
    lineHeight: 24,
    color: '#374151',
    marginBottom: 16,
  },
  lucidBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fef3c7',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    alignSelf: 'flex-start',
  },
  lucidText: {
    fontSize: 14,
    color: '#92400e',
    marginLeft: 6,
    fontWeight: '500',
  },
  aiSection: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 16,
  },
  aiButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#f8fafc',
    borderRadius: 12,
    marginBottom: 12,
  },
  aiButtonText: {
    flex: 1,
    fontSize: 16,
    fontWeight: '500',
    color: '#374151',
    marginLeft: 12,
  },
  premiumBadge: {
    backgroundColor: '#fbbf24',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  premiumText: {
    fontSize: 12,
    color: 'white',
    fontWeight: '600',
  },
});
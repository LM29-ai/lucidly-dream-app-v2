import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  FlatList,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useAuth } from '@/contexts/AuthContext';

// Mock dreams data for now
const mockDreams = [
  {
    id: '1',
    title: 'Flying Dream',
    content: 'I was soaring through clouds above my hometown...',
    created_at: '2025-01-15',
    mood: 'excited',
    is_lucid: true,
  },
  {
    id: '2', 
    title: 'Ocean Adventure',
    content: 'Swimming with dolphins in crystal clear waters...',
    created_at: '2025-01-14',
    mood: 'peaceful',
    is_lucid: false,
  },
];

export default function DreamsScreen() {
  const { user } = useAuth();
  const [dreams] = useState(mockDreams);

  const renderDream = ({ item }: any) => (
    <TouchableOpacity
      style={styles.dreamCard}
      onPress={() => router.push(`/dream/${item.id}` as any)}
    >
      <View style={styles.dreamHeader}>
        <Text style={styles.dreamTitle}>{item.title}</Text>
        {item.is_lucid && (
          <View style={styles.lucidBadge}>
            <Ionicons name="star" size={12} color="#fbbf24" />
            <Text style={styles.lucidText}>Lucid</Text>
          </View>
        )}
      </View>
      
      <Text style={styles.dreamContent} numberOfLines={2}>
        {item.content}
      </Text>
      
      <View style={styles.dreamFooter}>
        <Text style={styles.dreamDate}>{item.created_at}</Text>
        <View style={[styles.moodBadge, { backgroundColor: getMoodColor(item.mood) }]}>
          <Text style={styles.moodText}>{item.mood}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  const getMoodColor = (mood: string) => {
    switch (mood) {
      case 'excited': return '#ef4444';
      case 'peaceful': return '#10b981';
      case 'confused': return '#f59e0b';
      default: return '#6b7280';
    }
  };
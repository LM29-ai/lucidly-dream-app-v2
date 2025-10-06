// app/(tabs)/dreams.tsx
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  ListRenderItem,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
// If you don't have a TS path alias "@", use the relative path instead:
// import { useAuth } from '../../src/contexts/AuthContext';
import { useAuth } from '@/contexts/AuthContext';

type Dream = {
  id: string;
  title: string;
  content: string;
  created_at: string;
  mood: 'excited' | 'peaceful' | 'confused' | string;
  is_lucid: boolean;
};

const mockDreams: Dream[] = [
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

const getMoodColor = (mood: Dream['mood']) => {
  switch (mood) {
    case 'excited':
      return '#ef4444';
    case 'peaceful':
      return '#10b981';
    case 'confused':
      return '#f59e0b';
    default:
      return '#6b7280';
  }
};

export default function DreamsScreen() {
  const { user } = useAuth();
  const [dreams] = useState<Dream[]>(mockDreams);

  const renderDream: ListRenderItem<Dream> = ({ item }) => (
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
        <View
          style={[styles.moodBadge, { backgroundColor: getMoodColor(item.mood) }]}
        >
          <Text style={styles.moodText}>{item.mood}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        data={dreams}
        keyExtractor={(d) => d.id}
        renderItem={renderDream}
        contentContainerStyle={styles.listContent}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0b0f15',
  },
  listContent: {
    padding: 16,
    gap: 12,
  },
  dreamCard: {
    backgroundColor: '#111827',
    borderRadius: 12,
    padding: 14,
    gap: 8,
  },
  dreamHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  dreamTitle: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
    flexShrink: 1,
    marginRight: 8,
  },
  lucidBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#1f2937',
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  lucidText: {
    color: '#fbbf24',
    fontSize: 12,
    fontWeight: '600',
  },
  dreamContent: {
    color: '#cbd5e1',
    fontSize: 14,
  },
  dreamFooter: {
    marginTop: 4,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  dreamDate: {
    color: '#94a3b8',
    fontSize: 12,
  },
  moodBadge: {
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  moodText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
});

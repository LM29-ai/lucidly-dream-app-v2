import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';

export default function CreateDreamScreen() {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [mood, setMood] = useState('');
  const [isLucid, setIsLucid] = useState(false);
  const [loading, setLoading] = useState(false);

  const moods = [
    { name: 'Peaceful', icon: 'leaf', color: '#10b981' },
    { name: 'Excited', icon: 'flash', color: '#ef4444' },
    { name: 'Confused', icon: 'help-circle', color: '#f59e0b' },
    { name: 'Scary', icon: 'skull', color: '#6b7280' },
    { name: 'Happy', icon: 'happy', color: '#8b5cf6' },
  ];

  const handleSaveDream = async () => {
    if (!title.trim() || !content.trim()) {
      Alert.alert('Error', 'Please fill in both title and content');
      return;
    }

    setLoading(true);
    try {
      // TODO: Connect to real API later
      await new Promise(resolve => setTimeout(resolve, 1000)); // Mock delay
      
      Alert.alert('Success!', 'Dream saved successfully', [
        {
          text: 'View Dreams',
          onPress: () => router.replace('/dreams' as any)
        }
      ]);
      
      // Clear form
      setTitle('');
      setContent('');
      setMood('');
      setIsLucid(false);
      
    } catch (error) {
      Alert.alert('Error', 'Failed to save dream. Please try again.');
    } finally {
      setLoading(false);
    }
  };

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
        
        <Text style={styles.headerTitle}>Create Dream</Text>
        <Text style={styles.headerSubtitle}>Capture your dream experience</Text>
      </LinearGradient>

      <KeyboardAvoidingView
        style={styles.keyboardView}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView style={styles.form} showsVerticalScrollIndicator={false}>
          {/* Title Input */}
          <View style={styles.inputSection}>
            <Text style={styles.label}>Dream Title</Text>
            <TextInput
              style={styles.titleInput}
              placeholder="Give your dream a memorable title..."
              value={title}
              onChangeText={setTitle}
              maxLength={100}
            />
          </View>

          {/* Content Input */}
          <View style={styles.inputSection}>
            <Text style={styles.label}>Dream Description</Text>
            <TextInput
              style={styles.contentInput}
              placeholder="Describe your dream in vivid detail. What did you see, hear, and feel?..."
              value={content}
              onChangeText={setContent}
              multiline
              numberOfLines={6}
              textAlignVertical="top"
            />
          </View>

          {/* Mood Selection */}
          <View style={styles.inputSection}>
            <Text style={styles.label}>How did this dream make you feel?</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.moodContainer}>
              {moods.map((moodItem) => (
                <TouchableOpacity
                  key={moodItem.name}
                  style={[
                    styles.moodButton,
                    { backgroundColor: mood === moodItem.name ? moodItem.color : '#f3f4f6' },
                  ]}
                  onPress={() => setMood(mood === moodItem.name ? '' : moodItem.name)}
                >
                  <Ionicons
                    name={moodItem.icon as any}
                    size={20}
                    color={mood === moodItem.name ? 'white' : moodItem.color}
                  />
                  <Text
                    style={[
                      styles.moodText,
                      { color: mood === moodItem.name ? 'white' : moodItem.color }
                    ]}
                  >
                    {moodItem.name}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>

          {/* Lucid Dream Toggle */}
          <TouchableOpacity
            style={styles.lucidToggle}
            onPress={() => setIsLucid(!isLucid)}
          >
            <View style={styles.lucidToggleLeft}>
              <Ionicons
                name={isLucid ? 'checkmark-circle' : 'ellipse-outline'}
                size={24}
                color={isLucid ? '#10b981' : '#9ca3af'}
              />
              <View style={styles.lucidToggleText}>
                <Text style={styles.lucidLabel}>Lucid Dream</Text>
                <Text style={styles.lucidDescription}>
                  Were you aware you were dreaming?
                </Text>
              </View>
            </View>
            <Ionicons name="star" size={20} color="#fbbf24" />
          </TouchableOpacity>

          {/* Save Button */}
          <TouchableOpacity
            style={[styles.saveButton, loading && styles.saveButtonDisabled]}
            onPress={handleSaveDream}
            disabled={loading}
          >
            <Text style={styles.saveButtonText}>
              {loading ? 'Saving Dream...' : 'Save Dream'}
            </Text>
            <Ionicons name="checkmark" size={20} color="white" />
          </TouchableOpacity>
          
          <View style={{ height: 40 }} />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
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
    fontSize: 28,
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
  keyboardView: {
    flex: 1,
  },
  form: {
    flex: 1,
    padding: 16,
  },
  inputSection: {
    marginBottom: 24,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  titleInput: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  contentInput: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    height: 120,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  moodContainer: {
    flexDirection: 'row',
  },
  moodButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 20,
    marginRight: 12,
  },
  moodText: {
    marginLeft: 8,
    fontSize: 14,
    fontWeight: '500',
  },
  lucidToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  lucidToggleLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  lucidToggleText: {
    marginLeft: 12,
    flex: 1,
  },
  lucidLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
  },
  lucidDescription: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  saveButton: {
    backgroundColor: '#7c3aed',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  saveButtonDisabled: {
    opacity: 0.6,
  },
  saveButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: '600',
    marginRight: 8,
  },
});
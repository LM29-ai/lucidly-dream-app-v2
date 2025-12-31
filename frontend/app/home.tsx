import React from "react";
import { View, Text, Pressable } from "react-native";
import { useAuth } from "../src/contexts/AuthContext";
import { useRouter } from "expo-router";

export default function Home() {
  const router = useRouter();
  const { user, logout } = useAuth();

  async function onLogout() {
    await logout();
    router.replace("/login");
  }

  return (
    <View style={{ flex: 1, padding: 24, justifyContent: "center", gap: 16 }}>
      <Text style={{ fontSize: 22, fontWeight: "700" }}>Welcome</Text>
      <Text>{user?.email}</Text>

      <Pressable onPress={onLogout} style={{ padding: 14, borderRadius: 10, backgroundColor: "black" }}>
        <Text style={{ color: "white", textAlign: "center", fontWeight: "600" }}>Logout</Text>
      </Pressable>
    </View>
  );
}

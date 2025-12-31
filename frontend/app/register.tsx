import React, { useState } from "react";
import { View, Text, TextInput, Pressable } from "react-native";
import { useRouter } from "expo-router";
import { useAuth } from "../src/contexts/AuthContext";

export default function Register() {
  const router = useRouter();
  const { register } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);

  async function onRegister() {
    setErr(null);
    try {
      await register(email, password, name);
      router.replace("/home");
    } catch (e: any) {
      setErr(e?.message ?? "Registration failed");
    }
  }

  return (
    <View style={{ flex: 1, padding: 24, justifyContent: "center", gap: 12 }}>
      <Text style={{ fontSize: 24, fontWeight: "700" }}>Register</Text>
      {err ? <Text style={{ color: "red" }}>{err}</Text> : null}

      <TextInput placeholder="Name" value={name} onChangeText={setName}
        style={{ borderWidth: 1, padding: 12, borderRadius: 10 }} />
      <TextInput placeholder="Email" autoCapitalize="none" value={email} onChangeText={setEmail}
        style={{ borderWidth: 1, padding: 12, borderRadius: 10 }} />
      <TextInput placeholder="Password" secureTextEntry value={password} onChangeText={setPassword}
        style={{ borderWidth: 1, padding: 12, borderRadius: 10 }} />

      <Pressable onPress={onRegister} style={{ padding: 14, borderRadius: 10, backgroundColor: "black" }}>
        <Text style={{ color: "white", textAlign: "center", fontWeight: "600" }}>Create account</Text>
      </Pressable>

      <Pressable onPress={() => router.back()}>
        <Text style={{ textAlign: "center" }}>Back to login</Text>
      </Pressable>
    </View>
  );
}

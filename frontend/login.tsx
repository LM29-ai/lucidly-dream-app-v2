import React, { useState } from "react";
import { View, Text, TextInput, Pressable } from "react-native";
import { useRouter } from "expo-router";
import { useAuth } from "../src/contexts/AuthContext";

export default function Login() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);

  async function onLogin() {
    setErr(null);
    try {
      await login(email, password);
      router.replace("/home");
    } catch (e: any) {
      setErr(e?.message ?? "Login failed");
    }
  }

  return (
    <View style={{ flex: 1, padding: 24, justifyContent: "center", gap: 12 }}>
      <Text style={{ fontSize: 24, fontWeight: "700" }}>Login</Text>
      {err ? <Text style={{ color: "red" }}>{err}</Text> : null}

      <TextInput placeholder="Email" autoCapitalize="none" value={email} onChangeText={setEmail}
        style={{ borderWidth: 1, padding: 12, borderRadius: 10 }} />
      <TextInput placeholder="Password" secureTextEntry value={password} onChangeText={setPassword}
        style={{ borderWidth: 1, padding: 12, borderRadius: 10 }} />

      <Pressable onPress={onLogin} style={{ padding: 14, borderRadius: 10, backgroundColor: "black" }}>
        <Text style={{ color: "white", textAlign: "center", fontWeight: "600" }}>Sign in</Text>
      </Pressable>

      <Pressable onPress={() => router.push("/register")}>
        <Text style={{ textAlign: "center" }}>Create an account</Text>
      </Pressable>
    </View>
  );
}

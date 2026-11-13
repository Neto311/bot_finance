import React, { useEffect } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { Slot, useRouter, useSegments } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { AuthProvider, useAuth } from "../src/context/AuthContext";
import { CORES } from "../src/theme/colors";

function GuardiaoNavegacao() {
  const { usuario, carregando } = useAuth();
  const segmentos = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (carregando) return;

    const rotaAtual = segmentos[0];
    const emTelaPublica =
      rotaAtual === "login" ||
      rotaAtual === "registro" ||
      rotaAtual === "esqueci-senha";

    if (!usuario && !emTelaPublica) {
      router.replace("/login");
    } else if (usuario && emTelaPublica) {
      router.replace("/");
    }
  }, [usuario, carregando, segmentos]);

  if (carregando) {
    return (
      <View style={estilos.carregandoContainer}>
        <ActivityIndicator size="large" color={CORES.verde} />
      </View>
    );
  }

  return <Slot />;
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <StatusBar style="light" />
      <GuardiaoNavegacao />
    </AuthProvider>
  );
}

const estilos = StyleSheet.create({
  carregandoContainer: {
    flex: 1,
    backgroundColor: CORES.marinho,
    alignItems: "center",
    justifyContent: "center",
  },
});

import React, { useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { Link } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { useAuth } from "../src/context/AuthContext";

export default function TelaLogin() {
  const { entrar } = useAuth();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const handleLogin = async () => {
    if (!email.trim() || !senha) {
      setErro("Preencha seu e-mail e senha.");
      return;
    }

    setErro(null);
    setEnviando(true);
    try {
      await entrar(email, senha);
    } catch (e: any) {
      setErro(e?.message || "Falha ao entrar. Verifique suas credenciais.");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={estilos.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={estilos.card}>
        <View style={estilos.iconeContainer}>
          <Ionicons name="wallet-outline" size={38} color="#10b981" />
        </View>

        <Text style={estilos.titulo}>Bot Finança</Text>
        <Text style={estilos.subtitulo}>
          Seu assistente financeiro inteligente no estilo chat
        </Text>

        {erro ? (
          <View style={estilos.alertaErro}>
            <Ionicons name="alert-circle-outline" size={18} color="#f87171" />
            <Text style={estilos.textoErro}>{erro}</Text>
          </View>
        ) : null}

        <Text style={estilos.label}>E-mail</Text>
        <TextInput
          style={estilos.input}
          placeholder="seu@email.com"
          placeholderTextColor="#64748b"
          keyboardType="email-address"
          autoCapitalize="none"
          value={email}
          onChangeText={setEmail}
        />

        <Text style={estilos.label}>Senha</Text>
        <View style={estilos.senhaWrapper}>
          <TextInput
            style={estilos.inputSenha}
            placeholder="Sua senha"
            placeholderTextColor="#64748b"
            secureTextEntry={!mostrarSenha}
            value={senha}
            onChangeText={setSenha}
            onSubmitEditing={handleLogin}
          />
          <Pressable
            onPress={() => setMostrarSenha((v) => !v)}
            style={estilos.botaoOlho}
          >
            <Ionicons
              name={mostrarSenha ? "eye-off-outline" : "eye-outline"}
              size={20}
              color="#94a3b8"
            />
          </Pressable>
        </View>

        <Pressable
          style={[estilos.botaoPrimario, enviando && estilos.botaoDesabilitado]}
          onPress={handleLogin}
          disabled={enviando}
        >
          {enviando ? (
            <ActivityIndicator color="#052e16" />
          ) : (
            <Text style={estilos.textoBotaoPrimario}>Entrar</Text>
          )}
        </Pressable>

        <View style={estilos.rodape}>
          <Text style={estilos.textoRodape}>Ainda não tem conta? </Text>
          <Link href="/registro" asChild>
            <Pressable>
              <Text style={estilos.linkRodape}>Criar conta grátis</Text>
            </Pressable>
          </Link>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const estilos = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0b141a",
    justifyContent: "center",
    padding: 20,
  },
  card: {
    backgroundColor: "#111b21",
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: "#1f2c34",
    maxWidth: 440,
    width: "100%",
    alignSelf: "center",
  },
  iconeContainer: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: "rgba(16, 185, 129, 0.12)",
    alignItems: "center",
    justifyContent: "center",
    alignSelf: "center",
    marginBottom: 14,
  },
  titulo: {
    fontSize: 26,
    fontWeight: "700",
    color: "#f8fafc",
    textAlign: "center",
  },
  subtitulo: {
    fontSize: 14,
    color: "#94a3b8",
    textAlign: "center",
    marginTop: 6,
    marginBottom: 22,
  },
  alertaErro: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "rgba(239, 68, 68, 0.12)",
    borderColor: "rgba(239, 68, 68, 0.35)",
    borderWidth: 1,
    borderRadius: 10,
    padding: 10,
    marginBottom: 14,
    gap: 8,
  },
  textoErro: {
    color: "#fca5a5",
    fontSize: 13,
    flex: 1,
  },
  label: {
    color: "#cbd5e1",
    fontSize: 13,
    fontWeight: "600",
    marginBottom: 6,
    marginTop: 8,
  },
  input: {
    backgroundColor: "#202c33",
    color: "#f8fafc",
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    borderWidth: 1,
    borderColor: "#2a3942",
  },
  senhaWrapper: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#202c33",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#2a3942",
  },
  inputSenha: {
    flex: 1,
    color: "#f8fafc",
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
  },
  botaoOlho: {
    paddingHorizontal: 12,
  },
  botaoPrimario: {
    backgroundColor: "#10b981",
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 22,
  },
  botaoDesabilitado: {
    opacity: 0.65,
  },
  textoBotaoPrimario: {
    color: "#042f2e",
    fontSize: 16,
    fontWeight: "700",
  },
  rodape: {
    flexDirection: "row",
    justifyContent: "center",
    marginTop: 20,
  },
  textoRodape: {
    color: "#94a3b8",
    fontSize: 14,
  },
  linkRodape: {
    color: "#10b981",
    fontSize: 14,
    fontWeight: "700",
  },
});

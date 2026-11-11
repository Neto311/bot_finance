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

export default function TelaRegistro() {
  const { registrar } = useAuth();
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const handleRegistro = async () => {
    if (nome.trim().length < 2) {
      setErro("Informe seu nome (mínimo 2 caracteres).");
      return;
    }
    if (!email.trim().includes("@")) {
      setErro("Informe um e-mail válido.");
      return;
    }
    if (senha.length < 8) {
      setErro("A senha deve ter pelo menos 8 caracteres.");
      return;
    }

    setErro(null);
    setEnviando(true);
    try {
      await registrar(nome, email, senha);
    } catch (e: any) {
      setErro(e?.message || "Não foi possível criar sua conta.");
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
          <Ionicons name="person-add-outline" size={34} color="#10b981" />
        </View>

        <Text style={estilos.titulo}>Criar Conta</Text>
        <Text style={estilos.subtitulo}>
          Comece a registrar seus gastos por texto ou áudio em segundos
        </Text>

        {erro ? (
          <View style={estilos.alertaErro}>
            <Ionicons name="alert-circle-outline" size={18} color="#f87171" />
            <Text style={estilos.textoErro}>{erro}</Text>
          </View>
        ) : null}

        <Text style={estilos.label}>Como quer ser chamado?</Text>
        <TextInput
          style={estilos.input}
          placeholder="Ex: Neto"
          placeholderTextColor="#64748b"
          value={nome}
          onChangeText={setNome}
        />

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

        <Text style={estilos.label}>Senha (mín. 8 caracteres)</Text>
        <TextInput
          style={estilos.input}
          placeholder="••••••••"
          placeholderTextColor="#64748b"
          secureTextEntry
          value={senha}
          onChangeText={setSenha}
          onSubmitEditing={handleRegistro}
        />

        <Pressable
          style={[estilos.botaoPrimario, enviando && estilos.botaoDesabilitado]}
          onPress={handleRegistro}
          disabled={enviando}
        >
          {enviando ? (
            <ActivityIndicator color="#052e16" />
          ) : (
            <Text style={estilos.textoBotaoPrimario}>Criar minha conta</Text>
          )}
        </Pressable>

        <View style={estilos.rodape}>
          <Text style={estilos.textoRodape}>Já possui uma conta? </Text>
          <Link href="/login" asChild>
            <Pressable>
              <Text style={estilos.linkRodape}>Fazer login</Text>
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
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: "rgba(16, 185, 129, 0.12)",
    alignItems: "center",
    justifyContent: "center",
    alignSelf: "center",
    marginBottom: 14,
  },
  titulo: {
    fontSize: 24,
    fontWeight: "700",
    color: "#f8fafc",
    textAlign: "center",
  },
  subtitulo: {
    fontSize: 13,
    color: "#94a3b8",
    textAlign: "center",
    marginTop: 6,
    marginBottom: 20,
  },
  alertaErro: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "rgba(239, 68, 68, 0.12)",
    borderColor: "rgba(239, 68, 68, 0.35)",
    borderWidth: 1,
    borderRadius: 10,
    padding: 10,
    marginBottom: 12,
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
    marginTop: 18,
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

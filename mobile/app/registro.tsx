import React, { useState } from "react";
import {
  ActivityIndicator,
  Image,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Link } from "expo-router";
import { useAuth } from "../src/context/AuthContext";
import { CORES } from "../src/theme/colors";

export default function TelaRegistro() {
  const { registrar } = useAuth();
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const handleRegistro = async () => {
    if (nome.trim().length < 2) {
      setErro("Informe seu nome.");
      return;
    }
    if (!email.trim().includes("@")) {
      setErro("Informe um e-mail válido.");
      return;
    }
    if (senha.length < 8) {
      setErro("A senha precisa ter pelo menos 8 caracteres.");
      return;
    }

    setErro(null);
    setEnviando(true);
    try {
      await registrar(nome, email, senha);
    } catch (e: any) {
      setErro(e?.message || "Erro ao criar conta.");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <SafeAreaView style={estilos.safe}>
      <StatusBar barStyle="light-content" />
      <KeyboardAvoidingView
        style={estilos.container}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <View style={estilos.centro}>
          <Image
            source={require("../assets/logo.jpg")}
            style={estilos.logo}
            resizeMode="cover"
          />
          <Text style={estilos.titulo}>Criar conta</Text>

          {erro ? <Text style={estilos.erroTexto}>{erro}</Text> : null}

          <View style={estilos.form}>
            <TextInput
              style={estilos.input}
              placeholder="Nome"
              placeholderTextColor={CORES.textoSecundario}
              value={nome}
              onChangeText={setNome}
            />

            <TextInput
              style={estilos.input}
              placeholder="E-mail"
              placeholderTextColor={CORES.textoSecundario}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              value={email}
              onChangeText={setEmail}
            />

            <TextInput
              style={estilos.input}
              placeholder="Senha (mín. 8 caracteres)"
              placeholderTextColor={CORES.textoSecundario}
              secureTextEntry
              value={senha}
              onChangeText={setSenha}
              onSubmitEditing={handleRegistro}
            />

            <Pressable
              style={({ pressed }) => [
                estilos.botaoPrimario,
                (enviando || pressed) && { opacity: 0.85 },
              ]}
              onPress={handleRegistro}
              disabled={enviando}
            >
              {enviando ? (
                <ActivityIndicator color="#04131E" />
              ) : (
                <Text style={estilos.textoBotaoPrimario}>Cadastrar</Text>
              )}
            </Pressable>
          </View>
        </View>

        <View style={estilos.rodape}>
          <Text style={estilos.textoRodape}>Já tem uma conta? </Text>
          <Link href="/login" asChild>
            <Pressable hitSlop={8}>
              <Text style={estilos.linkRodape}>Entrar.</Text>
            </Pressable>
          </Link>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const estilos = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: CORES.fundo,
  },
  container: {
    flex: 1,
    justifyContent: "space-between",
  },
  centro: {
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: 28,
    maxWidth: 420,
    width: "100%",
    alignSelf: "center",
  },
  logo: {
    width: 72,
    height: 72,
    borderRadius: 36,
    alignSelf: "center",
    marginBottom: 14,
  },
  titulo: {
    fontSize: 26,
    fontWeight: "800",
    color: "#FFFFFF",
    textAlign: "center",
    letterSpacing: -0.4,
    marginBottom: 28,
  },
  erroTexto: {
    color: CORES.perigo,
    fontSize: 13,
    textAlign: "center",
    marginBottom: 14,
  },
  form: {
    gap: 12,
  },
  input: {
    height: 52,
    backgroundColor: CORES.superficieInput,
    borderRadius: 10,
    paddingHorizontal: 16,
    color: "#FFFFFF",
    fontSize: 15,
    borderWidth: 0.5,
    borderColor: CORES.bordaInput,
  },
  botaoPrimario: {
    height: 50,
    backgroundColor: CORES.verde,
    borderRadius: 25,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 8,
  },
  textoBotaoPrimario: {
    color: "#04131E",
    fontSize: 16,
    fontWeight: "700",
  },
  rodape: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    paddingVertical: 18,
    borderTopWidth: 0.5,
    borderTopColor: CORES.divisor,
  },
  textoRodape: {
    color: CORES.textoSecundario,
    fontSize: 13,
  },
  linkRodape: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "700",
  },
});

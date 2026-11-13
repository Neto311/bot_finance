import React, { useState } from "react";
import {
  ActivityIndicator,
  Alert,
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
import { Ionicons } from "@expo/vector-icons";
import { useAuth } from "../src/context/AuthContext";
import { CORES } from "../src/theme/colors";

export default function TelaLogin() {
  const { entrar } = useAuth();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const handleLogin = async () => {
    if (!email.trim() || !senha) {
      setErro("Insira seu e-mail e senha.");
      return;
    }

    setErro(null);
    setEnviando(true);
    try {
      await entrar(email, senha);
    } catch (e: any) {
      setErro(e?.message || "E-mail ou senha incorretos.");
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
        {/* Centro Limpo Estilo Instagram / Spotify (Sem Caixa / Card em volta) */}
        <View style={estilos.centro}>
          <Image
            source={require("../assets/logo.jpg")}
            style={estilos.logo}
            resizeMode="cover"
          />
          <Text style={estilos.marca}>
            Finace<Text style={{ color: CORES.dourado }}>Ai</Text>
          </Text>

          {erro ? <Text style={estilos.erroTexto}>{erro}</Text> : null}

          <View style={estilos.form}>
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

            <View style={estilos.inputSenhaBox}>
              <TextInput
                style={estilos.inputSenha}
                placeholder="Senha"
                placeholderTextColor={CORES.textoSecundario}
                secureTextEntry={!mostrarSenha}
                value={senha}
                onChangeText={setSenha}
                onSubmitEditing={handleLogin}
              />
              <Pressable
                onPress={() => setMostrarSenha((v) => !v)}
                hitSlop={10}
              >
                <Ionicons
                  name={mostrarSenha ? "eye-off" : "eye"}
                  size={20}
                  color={CORES.textoSecundario}
                />
              </Pressable>
            </View>

            <View style={{ alignItems: "flex-end" }}>
              <Link href="/esqueci-senha" asChild>
                <Pressable hitSlop={8}>
                  <Text style={estilos.linkEsqueciSenha}>
                    Esqueceu a senha?
                  </Text>
                </Pressable>
              </Link>
            </View>

            <Pressable
              style={({ pressed }) => [
                estilos.botaoEntrar,
                (enviando || pressed) && { opacity: 0.85 },
              ]}
              onPress={handleLogin}
              disabled={enviando}
            >
              {enviando ? (
                <ActivityIndicator color="#04131E" />
              ) : (
                <Text style={estilos.textoBotaoEntrar}>Entrar</Text>
              )}
            </Pressable>

            <View style={estilos.divisorRow}>
              <View style={estilos.linhaDivisor} />
              <Text style={estilos.textoOu}>OU</Text>
              <View style={estilos.linhaDivisor} />
            </View>

            <Pressable
              style={({ pressed }) => [
                estilos.botaoGoogle,
                pressed && { opacity: 0.75 },
              ]}
              onPress={() =>
                Alert.alert(
                  "Google Login",
                  "Vamos ativar a chave OAuth do Google Cloud no próximo passo!"
                )
              }
            >
              <Ionicons name="logo-google" size={18} color="#FFFFFF" />
              <Text style={estilos.textoBotaoGoogle}>Continuar com Google</Text>
            </Pressable>
          </View>
        </View>

        {/* Rodapé fixo na base estilo Instagram */}
        <View style={estilos.rodape}>
          <Text style={estilos.textoRodape}>Não tem uma conta? </Text>
          <Link href="/registro" asChild>
            <Pressable hitSlop={8}>
              <Text style={estilos.linkRodape}>Cadastre-se.</Text>
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
    width: 82,
    height: 82,
    borderRadius: 41,
    alignSelf: "center",
    marginBottom: 14,
  },
  marca: {
    fontSize: 32,
    fontWeight: "800",
    color: "#FFFFFF",
    textAlign: "center",
    letterSpacing: -0.5,
    marginBottom: 36,
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
  inputSenhaBox: {
    height: 52,
    backgroundColor: CORES.superficieInput,
    borderRadius: 10,
    paddingHorizontal: 16,
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 0.5,
    borderColor: CORES.bordaInput,
  },
  inputSenha: {
    flex: 1,
    color: "#FFFFFF",
    fontSize: 15,
    height: "100%",
  },
  linkEsqueciSenha: {
    color: CORES.verde,
    fontSize: 13,
    fontWeight: "600",
    marginTop: 2,
  },
  botaoEntrar: {
    height: 50,
    backgroundColor: CORES.verde,
    borderRadius: 25,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 8,
  },
  textoBotaoEntrar: {
    color: "#04131E",
    fontSize: 16,
    fontWeight: "700",
  },
  divisorRow: {
    flexDirection: "row",
    alignItems: "center",
    marginVertical: 14,
    gap: 14,
  },
  linhaDivisor: {
    flex: 1,
    height: 0.5,
    backgroundColor: CORES.bordaInput,
  },
  textoOu: {
    color: CORES.textoSecundario,
    fontSize: 12,
    fontWeight: "600",
  },
  botaoGoogle: {
    height: 50,
    borderRadius: 25,
    borderWidth: 1,
    borderColor: CORES.bordaInput,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
  },
  textoBotaoGoogle: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "600",
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

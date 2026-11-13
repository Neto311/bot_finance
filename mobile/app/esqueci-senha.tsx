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
import { Link, useRouter } from "expo-router";
import { apiAuth } from "../src/services/api";
import { CORES } from "../src/theme/colors";

export default function TelaEsqueciSenha() {
  const router = useRouter();
  const [etapa, setEtapa] = useState<1 | 2>(1);
  const [email, setEmail] = useState("");
  const [codigo, setCodigo] = useState("");
  const [novaSenha, setNovaSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const handleEnviarCodigo = async () => {
    if (!email.trim().includes("@")) {
      setErro("Informe seu e-mail cadastrado.");
      return;
    }

    setErro(null);
    setEnviando(true);
    try {
      await apiAuth.solicitarRecuperacaoSenha(email.trim());
      setEtapa(2);
    } catch (e: any) {
      setErro(e?.message || "Erro ao solicitar código.");
    } finally {
      setEnviando(false);
    }
  };

  const handleRedefinir = async () => {
    if (codigo.trim().length !== 6) {
      setErro("Digite o código de 6 dígitos.");
      return;
    }
    if (novaSenha.length < 8) {
      setErro("A nova senha deve ter pelo menos 8 caracteres.");
      return;
    }

    setErro(null);
    setEnviando(true);
    try {
      await apiAuth.redefinirSenha(email.trim(), codigo.trim(), novaSenha);
      Alert.alert(
        "Senha atualizada",
        "Sua senha foi redefinida com sucesso. Faça login com a nova senha."
      );
      router.replace("/login");
    } catch (e: any) {
      setErro(e?.message || "Código inválido ou expirado.");
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
          <Text style={estilos.titulo}>
            {etapa === 1 ? "Recuperar acesso" : "Código de segurança"}
          </Text>
          <Text style={estilos.subtitulo}>
            {etapa === 1
              ? "Insira seu e-mail para receber um código de 6 dígitos."
              : `Digite o código de 6 dígitos enviado para ${email} e escolha sua nova senha.`}
          </Text>

          {erro ? <Text style={estilos.erroTexto}>{erro}</Text> : null}

          {etapa === 1 ? (
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
                onSubmitEditing={handleEnviarCodigo}
              />

              <Pressable
                style={({ pressed }) => [
                  estilos.botaoPrimario,
                  (enviando || pressed) && { opacity: 0.85 },
                ]}
                onPress={handleEnviarCodigo}
                disabled={enviando}
              >
                {enviando ? (
                  <ActivityIndicator color="#04131E" />
                ) : (
                  <Text style={estilos.textoBotaoPrimario}>Enviar código</Text>
                )}
              </Pressable>
            </View>
          ) : (
            <View style={estilos.form}>
              <TextInput
                style={estilos.input}
                placeholder="Código de 6 dígitos"
                placeholderTextColor={CORES.textoSecundario}
                keyboardType="number-pad"
                maxLength={6}
                value={codigo}
                onChangeText={setCodigo}
              />

              <TextInput
                style={estilos.input}
                placeholder="Nova senha (mín. 8 caracteres)"
                placeholderTextColor={CORES.textoSecundario}
                secureTextEntry
                value={novaSenha}
                onChangeText={setNovaSenha}
                onSubmitEditing={handleRedefinir}
              />

              <Pressable
                style={({ pressed }) => [
                  estilos.botaoPrimario,
                  (enviando || pressed) && { opacity: 0.85 },
                ]}
                onPress={handleRedefinir}
                disabled={enviando}
              >
                {enviando ? (
                  <ActivityIndicator color="#04131E" />
                ) : (
                  <Text style={estilos.textoBotaoPrimario}>
                    Redefinir senha
                  </Text>
                )}
              </Pressable>
            </View>
          )}
        </View>

        <View style={estilos.rodape}>
          <Link href="/login" asChild>
            <Pressable hitSlop={8}>
              <Text style={estilos.linkRodape}>Voltar ao login</Text>
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
    width: 68,
    height: 68,
    borderRadius: 34,
    alignSelf: "center",
    marginBottom: 14,
  },
  titulo: {
    fontSize: 24,
    fontWeight: "800",
    color: "#FFFFFF",
    textAlign: "center",
    letterSpacing: -0.4,
  },
  subtitulo: {
    fontSize: 14,
    color: CORES.textoSecundario,
    textAlign: "center",
    marginTop: 8,
    marginBottom: 26,
    lineHeight: 20,
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
  linkRodape: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "700",
  },
});

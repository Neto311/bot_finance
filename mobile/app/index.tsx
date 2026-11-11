import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import {
  AudioModule,
  RecordingPresets,
  setAudioModeAsync,
  useAudioRecorder,
} from "expo-audio";
import { Ionicons } from "@expo/vector-icons";
import { useAuth } from "../src/context/AuthContext";
import { apiChat, apiFinancas } from "../src/services/api";
import { DadosTransacaoCard, MensagemChat } from "../src/types/api";
import { BolhaMensagem } from "../src/components/BolhaMensagem";
import { ModalEditarTransacao } from "../src/components/ModalEditarTransacao";
import { ModalIntegracao } from "../src/components/ModalIntegracao";

const ATALHOS_RAPIDOS = [
  { label: "📋 Últimos gastos", comando: "Listar meus últimos gastos" },
  { label: "💰 Meu saldo", comando: "Qual é o meu saldo atual?" },
  { label: "📊 Resumo do mês", comando: "Resumo dos meus gastos deste mês" },
];

export default function TelaChat() {
  const { usuario, sair, recarregarUsuario } = useAuth();
  const [mensagens, setMensagens] = useState<MensagemChat[]>([]);
  const [temMais, setTemMais] = useState(false);
  const [proximoCursor, setProximoCursor] = useState<number | null>(null);
  const [carregandoInicial, setCarregandoInicial] = useState(true);
  const [carregandoAnteriores, setCarregandoAnteriores] = useState(false);

  const [texto, setTexto] = useState("");
  const [assistenteDigitando, setAssistenteDigitando] = useState(false);

  // Gravação de áudio (expo-audio nativo do SDK 58)
  const gravadorAudio = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const [gravando, setGravando] = useState(false);
  const [segundosGravacao, setSegundosGravacao] = useState(0);

  // Modais
  const [transacaoEditando, setTransacaoEditando] =
    useState<DadosTransacaoCard | null>(null);
  const [modalIntegracaoVisivel, setModalIntegracaoVisivel] = useState(false);

  const flatListRef = useRef<FlatList<MensagemChat>>(null);

  useEffect(() => {
    carregarHistoricoInicial();
  }, []);

  useEffect(() => {
    let intervalo: ReturnType<typeof setInterval> | null = null;
    if (gravando) {
      setSegundosGravacao(0);
      intervalo = setInterval(() => {
        setSegundosGravacao((s) => s + 1);
      }, 1000);
    }
    return () => {
      if (intervalo) clearInterval(intervalo);
    };
  }, [gravando]);

  const carregarHistoricoInicial = async () => {
    setCarregandoInicial(true);
    try {
      const resp = await apiChat.listarMensagens(null, 30);
      setMensagens(resp.mensagens);
      setTemMais(resp.tem_mais);
      setProximoCursor(resp.proximo_cursor);
    } catch {
      // silencioso no primeiro carregamento
    } finally {
      setCarregandoInicial(false);
    }
  };

  const carregarMensagensAnteriores = async () => {
    if (!temMais || !proximoCursor || carregandoAnteriores) return;
    setCarregandoAnteriores(true);
    try {
      const resp = await apiChat.listarMensagens(proximoCursor, 30);
      setMensagens((atuais) => [...resp.mensagens, ...atuais]);
      setTemMais(resp.tem_mais);
      setProximoCursor(resp.proximo_cursor);
    } finally {
      setCarregandoAnteriores(false);
    }
  };

  const enviarMensagemTexto = async (conteudoEnvio?: string) => {
    const textoLimpo = (conteudoEnvio ?? texto).trim();
    if (!textoLimpo || assistenteDigitando) return;

    if (!conteudoEnvio) setTexto("");

    const idTemporario = -Date.now();
    const msgOtimista: MensagemChat = {
      id: idTemporario,
      remetente: "usuario",
      tipo: "texto",
      conteudo: textoLimpo,
      criado_em: new Date().toISOString(),
    };

    setMensagens((atuais) => [...atuais, msgOtimista]);
    setAssistenteDigitando(true);

    try {
      const resp = await apiChat.enviarTexto(textoLimpo);
      setMensagens((atuais) => [
        ...atuais.filter((m) => m.id !== idTemporario),
        resp.mensagem_usuario,
        resp.mensagem_assistente,
      ]);
      recarregarUsuario();
    } catch (e: any) {
      const msgErro: MensagemChat = {
        id: -Date.now() - 1,
        remetente: "assistente",
        tipo: "texto",
        conteudo: `⚠️ Não consegui processar agora: ${
          e?.message || "Erro de conexão"
        }`,
        criado_em: new Date().toISOString(),
      };
      setMensagens((atuais) => [...atuais, msgErro]);
    } finally {
      setAssistenteDigitando(false);
    }
  };

  const iniciarGravacaoAudio = async () => {
    try {
      const permissao = await AudioModule.requestRecordingPermissionsAsync();
      if (!permissao.granted) {
        Alert.alert(
          "Permissão de Microfone",
          "Permita o uso do microfone nos Ajustes do iPhone para gravar seus gastos por voz."
        );
        return;
      }

      await setAudioModeAsync({
        allowsRecording: true,
        playsInSilentMode: true,
      });

      await gravadorAudio.prepareToRecordAsync();
      gravadorAudio.record();
      setGravando(true);
    } catch (e: any) {
      Alert.alert(
        "Erro ao iniciar gravação",
        e?.message || "Não foi possível acessar o microfone."
      );
    }
  };

  const pararEEnviarGravacaoAudio = async () => {
    if (!gravando) return;
    const duracao = segundosGravacao;
    setGravando(false);

    try {
      await gravadorAudio.stop();
      const uri = gravadorAudio.uri;
      if (!uri) return;

      setAssistenteDigitando(true);
      const resp = await apiChat.enviarAudio(uri, duracao);
      setMensagens((atuais) => [
        ...atuais,
        resp.mensagem_usuario,
        resp.mensagem_assistente,
      ]);
      recarregarUsuario();
    } catch (e: any) {
      const msgErro: MensagemChat = {
        id: -Date.now(),
        remetente: "assistente",
        tipo: "texto",
        conteudo: `⚠️ Erro ao transcrever áudio: ${
          e?.message || "Tente novamente"
        }`,
        criado_em: new Date().toISOString(),
      };
      setMensagens((atuais) => [...atuais, msgErro]);
    } finally {
      setAssistenteDigitando(false);
    }
  };

  const handleSalvarEdicaoTransacao = async (
    numeroUsuario: number,
    dados: {
      valor: number;
      categoria: string;
      descricao: string;
      tipo: string;
      data: string;
    }
  ) => {
    await apiFinancas.editarTransacao(numeroUsuario, dados);
    setMensagens((atuais) =>
      atuais.map((m) => {
        if (
          m.tipo === "card_transacao" &&
          m.dados_extras?.numero_usuario === numeroUsuario
        ) {
          return {
            ...m,
            conteudo: `Gasto editado: ${dados.descricao} - R$ ${dados.valor.toFixed(
              2
            )}`,
            dados_extras: {
              ...m.dados_extras,
              ...dados,
            },
          };
        }
        return m;
      })
    );
  };

  const handleExcluirTransacao = async (numeroUsuario: number) => {
    try {
      await apiFinancas.excluirTransacao(numeroUsuario);
      setMensagens((atuais) =>
        atuais.map((m) => {
          if (
            m.tipo === "card_transacao" &&
            m.dados_extras?.numero_usuario === numeroUsuario
          ) {
            return {
              ...m,
              dados_extras: {
                ...m.dados_extras,
                excluida: true,
              },
            };
          }
          return m;
        })
      );
    } catch {
      // ignora erro se já excluída
    }
  };

  return (
    <SafeAreaView style={estilos.safeArea}>
      {/* Header estilo WhatsApp Financeiro */}
      <View style={estilos.header}>
        <View style={estilos.avatarAssistente}>
          <Ionicons name="sparkles" size={20} color="#10b981" />
        </View>

        <View style={{ flex: 1 }}>
          <Text style={estilos.nomeHeader}>Assistente Bot Finança</Text>
          <Text style={estilos.subtituloHeader}>
            Olá, {usuario?.nome?.split(" ")[0] || "Usuário"} • Modo:{" "}
            {usuario?.provedor_principal === "minhas_economias"
              ? "Minhas Economias"
              : "Local"}
          </Text>
        </View>

        <Pressable
          style={estilos.botaoHeader}
          onPress={() => setModalIntegracaoVisivel(true)}
        >
          <Ionicons name="settings-outline" size={21} color="#cbd5e1" />
        </Pressable>

        <Pressable style={estilos.botaoHeader} onPress={sair}>
          <Ionicons name="log-out-outline" size={22} color="#f87171" />
        </Pressable>
      </View>

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        {carregandoInicial ? (
          <View style={estilos.centroContainer}>
            <ActivityIndicator size="large" color="#10b981" />
          </View>
        ) : (
          <FlatList
            ref={flatListRef}
            data={mensagens}
            keyExtractor={(item) => String(item.id)}
            contentContainerStyle={estilos.listaConteudo}
            onContentSizeChange={() =>
              flatListRef.current?.scrollToEnd({ animated: true })
            }
            ListHeaderComponent={
              temMais ? (
                <Pressable
                  style={estilos.botaoCarregarMais}
                  onPress={carregarMensagensAnteriores}
                  disabled={carregandoAnteriores}
                >
                  {carregandoAnteriores ? (
                    <ActivityIndicator size="small" color="#10b981" />
                  ) : (
                    <Text style={estilos.textoCarregarMais}>
                      Carregar mensagens anteriores
                    </Text>
                  )}
                </Pressable>
              ) : (
                <View style={estilos.boasVindasCard}>
                  <Text style={estilos.boasVindasTexto}>
                    👋 Envie um gasto como{" "}
                    <Text style={{ fontWeight: "700", color: "#34d399" }}>
                      "Almoço 35"
                    </Text>{" "}
                    ou segure o microfone para falar!
                  </Text>
                </View>
              )
            }
            renderItem={({ item }) => (
              <BolhaMensagem
                mensagem={item}
                onEditarTransacao={(t) => setTransacaoEditando(t)}
                onExcluirTransacao={handleExcluirTransacao}
              />
            )}
            ListFooterComponent={
              assistenteDigitando ? (
                <View style={estilos.digitandoContainer}>
                  <ActivityIndicator size="small" color="#10b981" />
                  <Text style={estilos.digitandoTexto}>
                    Assistente está analisando...
                  </Text>
                </View>
              ) : null
            }
          />
        )}

        {/* Chips de Ação Rápida (1 toque) */}
        <View style={estilos.barraChips}>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={estilos.scrollChips}
          >
            {ATALHOS_RAPIDOS.map((atalho) => (
              <Pressable
                key={atalho.label}
                style={estilos.chipAcao}
                onPress={() => enviarMensagemTexto(atalho.comando)}
              >
                <Text style={estilos.textoChipAcao}>{atalho.label}</Text>
              </Pressable>
            ))}
            <Pressable
              style={estilos.chipAcao}
              onPress={() => setModalIntegracaoVisivel(true)}
            >
              <Text style={estilos.textoChipAcao}>⚙️ Integrações</Text>
            </Pressable>
          </ScrollView>
        </View>

        {/* Barra de Entrada de Mensagem / Áudio */}
        <View style={estilos.barraEntrada}>
          {gravando ? (
            <View style={estilos.gravandoBox}>
              <View style={estilos.pontoVermelho} />
              <Text style={estilos.gravandoTexto}>
                Gravando áudio... {segundosGravacao}s
              </Text>
            </View>
          ) : (
            <TextInput
              style={estilos.inputMensagem}
              placeholder="Ex: Mercado 142.50 ou 'Qual meu saldo?'"
              placeholderTextColor="#64748b"
              value={texto}
              onChangeText={setTexto}
              onSubmitEditing={() => enviarMensagemTexto()}
            />
          )}

          {texto.trim().length > 0 ? (
            <Pressable
              style={estilos.botaoRedondo}
              onPress={() => enviarMensagemTexto()}
            >
              <Ionicons name="send" size={19} color="#042f2e" />
            </Pressable>
          ) : (
            <Pressable
              style={[
                estilos.botaoRedondo,
                gravando && estilos.botaoGravandoAtivo,
              ]}
              onPress={
                gravando ? pararEEnviarGravacaoAudio : iniciarGravacaoAudio
              }
            >
              <Ionicons
                name={gravando ? "stop" : "mic"}
                size={22}
                color={gravando ? "#fff" : "#042f2e"}
              />
            </Pressable>
          )}
        </View>
      </KeyboardAvoidingView>

      <ModalEditarTransacao
        visivel={Boolean(transacaoEditando)}
        transacao={transacaoEditando}
        onFechar={() => setTransacaoEditando(null)}
        onSalvar={handleSalvarEdicaoTransacao}
      />

      <ModalIntegracao
        visivel={modalIntegracaoVisivel}
        provedorAtual={usuario?.provedor_principal ?? "local"}
        onFechar={() => setModalIntegracaoVisivel(false)}
        onAtualizado={recarregarUsuario}
      />
    </SafeAreaView>
  );
}

const estilos = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#0b141a",
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#202c33",
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#2a3942",
    gap: 10,
  },
  avatarAssistente: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "rgba(16, 185, 129, 0.14)",
    alignItems: "center",
    justifyContent: "center",
  },
  nomeHeader: {
    color: "#f8fafc",
    fontSize: 16,
    fontWeight: "700",
  },
  subtituloHeader: {
    color: "#94a3b8",
    fontSize: 12,
    marginTop: 1,
  },
  botaoHeader: {
    padding: 8,
    borderRadius: 10,
    backgroundColor: "#111b21",
  },
  centroContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  listaConteudo: {
    paddingVertical: 12,
  },
  boasVindasCard: {
    alignSelf: "center",
    backgroundColor: "#182229",
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 12,
    marginBottom: 12,
    maxWidth: "88%",
    borderWidth: 1,
    borderColor: "#2a3942",
  },
  boasVindasTexto: {
    color: "#cbd5e1",
    fontSize: 13,
    textAlign: "center",
  },
  botaoCarregarMais: {
    alignSelf: "center",
    backgroundColor: "#202c33",
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 16,
    marginBottom: 10,
  },
  textoCarregarMais: {
    color: "#10b981",
    fontSize: 12,
    fontWeight: "600",
  },
  digitandoContainer: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 18,
    paddingVertical: 8,
  },
  digitandoTexto: {
    color: "#94a3b8",
    fontSize: 13,
    fontStyle: "italic",
  },
  barraChips: {
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: "#1f2c34",
    backgroundColor: "#111b21",
  },
  scrollChips: {
    paddingHorizontal: 12,
    gap: 8,
  },
  chipAcao: {
    backgroundColor: "#202c33",
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: "#2a3942",
  },
  textoChipAcao: {
    color: "#e2e8f0",
    fontSize: 12,
    fontWeight: "600",
  },
  barraEntrada: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 10,
    paddingVertical: 8,
    backgroundColor: "#111b21",
    gap: 8,
  },
  inputMensagem: {
    flex: 1,
    backgroundColor: "#202c33",
    color: "#f8fafc",
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 11,
    fontSize: 15,
    borderWidth: 1,
    borderColor: "#2a3942",
  },
  gravandoBox: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "rgba(239, 68, 68, 0.15)",
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 11,
    gap: 8,
  },
  pontoVermelho: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: "#ef4444",
  },
  gravandoTexto: {
    color: "#fca5a5",
    fontSize: 14,
    fontWeight: "600",
  },
  botaoRedondo: {
    width: 46,
    height: 46,
    borderRadius: 23,
    backgroundColor: "#10b981",
    alignItems: "center",
    justifyContent: "center",
  },
  botaoGravandoAtivo: {
    backgroundColor: "#ef4444",
  },
});

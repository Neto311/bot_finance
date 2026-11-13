import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Image,
  Keyboard,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
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
import { apiAuth, apiChat, apiFinancas } from "../src/services/api";
import { DadosTransacaoCard, MensagemChat } from "../src/types/api";
import { BolhaMensagem } from "../src/components/BolhaMensagem";
import { ModalEditarTransacao } from "../src/components/ModalEditarTransacao";
import { ModalIntegracao } from "../src/components/ModalIntegracao";
import { VisaoDashboard } from "../src/components/VisaoDashboard";
import { CORES } from "../src/theme/colors";

const SUGESTOES = [
  { label: "Analisar finanças", comando: "Analise minhas finanças deste mês" },
  { label: "Resumo do mês", comando: "Resumo dos meus gastos deste mês" },
  { label: "Meu saldo", comando: "Qual é o meu saldo atual?" },
  { label: "Recentes", comando: "Listar meus últimos gastos" },
];

export default function TelaPrincipal() {
  const { usuario, sair, recarregarUsuario } = useAuth();
  const [abaAtiva, setAbaAtiva] = useState<"dashboard" | "chat" | "perfil">(
    "chat"
  );

  const [mensagens, setMensagens] = useState<MensagemChat[]>([]);
  const [temMais, setTemMais] = useState(false);
  const [proximoCursor, setProximoCursor] = useState<number | null>(null);
  const [carregandoInicial, setCarregandoInicial] = useState(true);
  const [carregandoAnteriores, setCarregandoAnteriores] = useState(false);

  const [texto, setTexto] = useState("");
  const [assistenteDigitando, setAssistenteDigitando] = useState(false);
  const [tecladoAberto, setTecladoAberto] = useState(false);

  const gravadorAudio = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const [gravando, setGravando] = useState(false);
  const [segundosGravacao, setSegundosGravacao] = useState(0);

  const [transacaoEditando, setTransacaoEditando] =
    useState<DadosTransacaoCard | null>(null);
  const [modalIntegracaoVisivel, setModalIntegracaoVisivel] = useState(false);

  const flatListRef = useRef<FlatList<MensagemChat>>(null);

  useEffect(() => {
    carregarHistoricoInicial();
  }, []);

  useEffect(() => {
    const eventoAbrir =
      Platform.OS === "ios" ? "keyboardWillShow" : "keyboardDidShow";
    const eventoFechar =
      Platform.OS === "ios" ? "keyboardWillHide" : "keyboardDidHide";

    const subAbrir = Keyboard.addListener(eventoAbrir, () => {
      setTecladoAberto(true);
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 80);
    });
    const subFechar = Keyboard.addListener(eventoFechar, () => {
      setTecladoAberto(false);
    });

    return () => {
      subAbrir.remove();
      subFechar.remove();
    };
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
      // silencioso
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
        conteudo: e?.message || "Erro de conexão",
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
        Alert.alert("Microfone", "Permita o acesso ao microfone nos Ajustes.");
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
      Alert.alert("Erro", e?.message || "Falha ao gravar.");
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
        conteudo: e?.message || "Não foi possível transcrever.",
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
    recarregarUsuario();
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
      recarregarUsuario();
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
      // silencioso
    }
  };

  const renderizarPerfil = () => (
    <View style={estilos.perfilContainer}>
      <View style={estilos.perfilTopo}>
        <View style={estilos.avatarGrande}>
          <Text style={estilos.inicialAvatar}>
            {(usuario?.nome?.[0] || "F").toUpperCase()}
          </Text>
        </View>
        <Text style={estilos.nomePerfil}>{usuario?.nome || "Usuário"}</Text>
        <Text style={estilos.emailPerfil}>{usuario?.email}</Text>
      </View>

      <View style={estilos.menuLista}>
        <Pressable
          style={estilos.menuItem}
          onPress={() => setModalIntegracaoVisivel(true)}
        >
          <Ionicons name="sync-outline" size={22} color="#FFFFFF" />
          <View style={{ flex: 1 }}>
            <Text style={estilos.menuTitulo}>Sincronização</Text>
            <Text style={estilos.menuSub}>
              {usuario?.provedor_principal === "minhas_economias"
                ? "Minhas Economias"
                : "Nuvem FinaceAi"}
            </Text>
          </View>
          <Ionicons
            name="chevron-forward"
            size={18}
            color={CORES.textoSecundario}
          />
        </Pressable>

        <Pressable style={estilos.menuItem} onPress={sair}>
          <Ionicons name="log-out-outline" size={22} color="#FFFFFF" />
          <Text style={[estilos.menuTitulo, { flex: 1 }]}>Sair da conta</Text>
        </Pressable>

        <Pressable
          style={estilos.menuItem}
          onPress={() => {
            Alert.alert(
              "Excluir conta",
              "Tem certeza que deseja excluir permanentemente sua conta e todos os seus dados financeiros?",
              [
                { text: "Cancelar", style: "cancel" },
                {
                  text: "Excluir conta",
                  style: "destructive",
                  onPress: async () => {
                    try {
                      await apiAuth.excluirMinhaConta();
                      await sair();
                    } catch (e: any) {
                      Alert.alert(
                        "Erro",
                        e?.message || "Não foi possível excluir sua conta."
                      );
                    }
                  },
                },
              ]
            );
          }}
        >
          <Ionicons name="trash-outline" size={22} color={CORES.perigo} />
          <Text style={[estilos.menuTitulo, { color: CORES.perigo, flex: 1 }]}>
            Excluir minha conta
          </Text>
        </Pressable>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={estilos.safeArea} edges={["top", "left", "right"]}>
      <StatusBar barStyle="light-content" />

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        keyboardVerticalOffset={Platform.OS === "ios" ? 0 : 0}
      >
        {/* Header Minimalista estilo Instagram Direct / Spotify */}
        <View style={estilos.header}>
          <Image
            source={require("../assets/logo.jpg")}
            style={estilos.logoMini}
          />
          <Text style={estilos.tituloHeader}>
            Finace<Text style={{ color: CORES.dourado }}>Ai</Text>
          </Text>
        </View>

        {/* Conteúdo da Aba Selecionada */}
        <View style={{ flex: 1 }}>
          {abaAtiva === "dashboard" ? (
            <VisaoDashboard
              usuario={usuario}
              onEditarTransacao={(t) => setTransacaoEditando(t)}
              onExcluirTransacao={handleExcluirTransacao}
              onSaldoAtualizado={recarregarUsuario}
              onIrParaChat={(cmd) => {
                setAbaAtiva("chat");
                if (cmd) enviarMensagemTexto(cmd);
              }}
            />
          ) : abaAtiva === "perfil" ? (
            renderizarPerfil()
          ) : (
            <View style={{ flex: 1 }}>
              {carregandoInicial ? (
                <View style={estilos.centroContainer}>
                  <ActivityIndicator size="large" color={CORES.verde} />
                </View>
              ) : (
                <FlatList
                  ref={flatListRef}
                  data={mensagens}
                  keyExtractor={(item) => String(item.id)}
                  contentContainerStyle={estilos.listaConteudo}
                  keyboardDismissMode="interactive"
                  keyboardShouldPersistTaps="handled"
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
                        <Text style={estilos.textoCarregarMais}>
                          Ver anteriores
                        </Text>
                      </Pressable>
                    ) : null
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
                      <View style={estilos.digitandoRow}>
                        <ActivityIndicator size="small" color={CORES.verde} />
                      </View>
                    ) : null
                  }
                />
              )}

              {/* Sugestões discretas horizontais */}
              <View style={estilos.sugestoesWrapper}>
                <ScrollView
                  horizontal
                  showsHorizontalScrollIndicator={false}
                  keyboardShouldPersistTaps="handled"
                  contentContainerStyle={estilos.sugestoesScroll}
                >
                  {SUGESTOES.map((s) => (
                    <Pressable
                      key={s.label}
                      style={estilos.pilulaSugestao}
                      onPress={() => enviarMensagemTexto(s.comando)}
                    >
                      <Text style={estilos.textoSugestao}>{s.label}</Text>
                    </Pressable>
                  ))}
                </ScrollView>
              </View>

              {/* Barra Cápsula Única estilo WhatsApp / Instagram Direct que sobe junto com o teclado */}
              <View
                style={[
                  estilos.inputWrapper,
                  tecladoAberto && { paddingBottom: 10 },
                ]}
              >
                <View style={estilos.capsulaInput}>
                  {gravando ? (
                    <View style={estilos.gravandoRow}>
                      <View style={estilos.bolinhaGravando} />
                      <Text style={estilos.textoGravando}>
                        Gravando... {segundosGravacao}s
                      </Text>
                    </View>
                  ) : (
                    <TextInput
                      style={estilos.inputTexto}
                      placeholder="Mensagem..."
                      placeholderTextColor={CORES.textoSecundario}
                      value={texto}
                      onChangeText={setTexto}
                      onSubmitEditing={() => enviarMensagemTexto()}
                    />
                  )}

                  {texto.trim().length > 0 ? (
                    <Pressable
                      style={estilos.botaoEnviarDentro}
                      onPress={() => enviarMensagemTexto()}
                    >
                      <Text style={estilos.textoBotaoEnviar}>Enviar</Text>
                    </Pressable>
                  ) : (
                    <Pressable
                      style={[
                        estilos.botaoMicDentro,
                        gravando && { backgroundColor: CORES.perigo },
                      ]}
                      onPress={
                        gravando
                          ? pararEEnviarGravacaoAudio
                          : iniciarGravacaoAudio
                      }
                    >
                      <Ionicons
                        name={gravando ? "stop" : "mic-outline"}
                        size={20}
                        color="#FFFFFF"
                      />
                    </Pressable>
                  )}
                </View>
              </View>
            </View>
          )}
        </View>

        {/* Bottom Tab Bar Nativa (oculta automaticamente quando o teclado está aberto igual ao WhatsApp/Instagram DM) */}
        {!tecladoAberto ? (
          <View style={estilos.bottomTabBar}>
            <Pressable
              style={estilos.tabItem}
              onPress={() => setAbaAtiva("dashboard")}
            >
              <Ionicons
                name={abaAtiva === "dashboard" ? "home" : "home-outline"}
                size={24}
                color={
                  abaAtiva === "dashboard" ? "#FFFFFF" : CORES.textoSecundario
                }
              />
              <Text
                style={[
                  estilos.tabLabel,
                  abaAtiva === "dashboard" && estilos.tabLabelAtivo,
                ]}
              >
                Início
              </Text>
            </Pressable>

            <Pressable
              style={estilos.tabItem}
              onPress={() => setAbaAtiva("chat")}
            >
              <Ionicons
                name={
                  abaAtiva === "chat"
                    ? "chatbubble-ellipses"
                    : "chatbubble-ellipses-outline"
                }
                size={24}
                color={abaAtiva === "chat" ? "#FFFFFF" : CORES.textoSecundario}
              />
              <Text
                style={[
                  estilos.tabLabel,
                  abaAtiva === "chat" && estilos.tabLabelAtivo,
                ]}
              >
                Chat
              </Text>
            </Pressable>

            <Pressable
              style={estilos.tabItem}
              onPress={() => setAbaAtiva("perfil")}
            >
              <Ionicons
                name={abaAtiva === "perfil" ? "person" : "person-outline"}
                size={24}
                color={
                  abaAtiva === "perfil" ? "#FFFFFF" : CORES.textoSecundario
                }
              />
              <Text
                style={[
                  estilos.tabLabel,
                  abaAtiva === "perfil" && estilos.tabLabelAtivo,
                ]}
              >
                Conta
              </Text>
            </Pressable>
          </View>
        ) : null}
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
    backgroundColor: CORES.fundo,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingVertical: 12,
    gap: 10,
  },
  logoMini: {
    width: 30,
    height: 30,
    borderRadius: 15,
  },
  tituloHeader: {
    color: "#FFFFFF",
    fontSize: 20,
    fontWeight: "800",
    letterSpacing: -0.4,
  },
  centroContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  listaConteudo: {
    paddingVertical: 12,
  },
  botaoCarregarMais: {
    alignSelf: "center",
    paddingVertical: 8,
    marginBottom: 8,
  },
  textoCarregarMais: {
    color: CORES.textoSecundario,
    fontSize: 12,
    fontWeight: "600",
  },
  digitandoRow: {
    paddingHorizontal: 22,
    paddingVertical: 8,
    alignItems: "flex-start",
  },
  sugestoesWrapper: {
    paddingVertical: 6,
  },
  sugestoesScroll: {
    paddingHorizontal: 16,
    gap: 8,
  },
  pilulaSugestao: {
    backgroundColor: CORES.fundoElevado,
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 18,
  },
  textoSugestao: {
    color: CORES.textoSecundario,
    fontSize: 13,
    fontWeight: "600",
  },
  inputWrapper: {
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  capsulaInput: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: CORES.fundoElevado,
    borderRadius: 26,
    paddingLeft: 18,
    paddingRight: 6,
    height: 48,
  },
  inputTexto: {
    flex: 1,
    color: "#FFFFFF",
    fontSize: 15,
    height: "100%",
  },
  gravandoRow: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  bolinhaGravando: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: CORES.perigo,
  },
  textoGravando: {
    color: CORES.perigo,
    fontSize: 14,
    fontWeight: "600",
  },
  botaoEnviarDentro: {
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  textoBotaoEnviar: {
    color: CORES.verde,
    fontSize: 15,
    fontWeight: "700",
  },
  botaoMicDentro: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
  },
  bottomTabBar: {
    flexDirection: "row",
    backgroundColor: CORES.fundo,
    borderTopWidth: 0.5,
    borderTopColor: CORES.divisor,
    paddingTop: 8,
    paddingBottom: Platform.OS === "ios" ? 22 : 10,
  },
  tabItem: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 3,
  },
  tabLabel: {
    color: CORES.textoSecundario,
    fontSize: 10,
    fontWeight: "600",
  },
  tabLabelAtivo: {
    color: "#FFFFFF",
  },
  perfilContainer: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 24,
  },
  perfilTopo: {
    alignItems: "center",
    marginBottom: 36,
  },
  avatarGrande: {
    width: 76,
    height: 76,
    borderRadius: 38,
    backgroundColor: CORES.fundoElevado,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
  },
  inicialAvatar: {
    color: CORES.dourado,
    fontSize: 28,
    fontWeight: "800",
  },
  nomePerfil: {
    color: "#FFFFFF",
    fontSize: 20,
    fontWeight: "700",
  },
  emailPerfil: {
    color: CORES.textoSecundario,
    fontSize: 14,
    marginTop: 2,
  },
  menuLista: {
    gap: 4,
  },
  menuItem: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 16,
    gap: 14,
    borderBottomWidth: 0.5,
    borderBottomColor: CORES.divisor,
  },
  menuTitulo: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
  },
  menuSub: {
    color: CORES.textoSecundario,
    fontSize: 13,
    marginTop: 2,
  },
});

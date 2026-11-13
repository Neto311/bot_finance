import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Modal,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { apiFinancas } from "../services/api";
import { DadosTransacaoCard, UsuarioAuth } from "../types/api";
import { CORES, iconePorCategoria } from "../theme/colors";

interface Props {
  usuario: UsuarioAuth | null;
  onEditarTransacao: (transacao: DadosTransacaoCard) => void;
  onExcluirTransacao: (numeroUsuario: number) => Promise<void>;
  onSaldoAtualizado?: () => Promise<void>;
  onIrParaChat: (comando?: string) => void;
}

const NOMES_MESES = [
  "Jan",
  "Fev",
  "Mar",
  "Abr",
  "Mai",
  "Jun",
  "Jul",
  "Ago",
  "Set",
  "Out",
  "Nov",
  "Dez",
];

function formatarMoeda(valor: number): string {
  return Number(valor || 0).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

export function VisaoDashboard({
  usuario,
  onEditarTransacao,
  onExcluirTransacao,
  onSaldoAtualizado,
}: Props) {
  const hoje = new Date();
  const [mes, setMes] = useState(hoje.getMonth() + 1);
  const [ano, setAno] = useState(hoje.getFullYear());
  const [carregando, setCarregando] = useState(true);
  const [atualizando, setAtualizando] = useState(false);

  const [gastoTotal, setGastoTotal] = useState(0);
  const [ganhoTotal, setGanhoTotal] = useState(0);
  const [categorias, setCategorias] = useState<Record<string, number>>({});
  const [lancamentosMes, setLancamentosMes] = useState<DadosTransacaoCard[]>([]);

  // Filtros por categoria / busca por data ou descrição
  const [categoriaFiltro, setCategoriaFiltro] = useState<string | null>(null);
  const [buscaDataOuTexto, setBuscaDataOuTexto] = useState("");

  // Modal de edição rápida de saldo (PUT /saldo)
  const [modalSaldoVisivel, setModalSaldoVisivel] = useState(false);
  const [novoSaldoInput, setNovoSaldoInput] = useState("");
  const [salvandoSaldo, setSalvandoSaldo] = useState(false);

  const carregarDados = useCallback(async () => {
    try {
      const [resumoResp, listaResp] = await Promise.all([
        apiFinancas.obterResumoMes(mes, ano),
        apiFinancas.listarPorMes(mes, ano),
      ]);
      setGastoTotal(Number(resumoResp?.gasto_total || 0));
      setGanhoTotal(Number(resumoResp?.ganho_total || 0));
      setCategorias(resumoResp?.categorias || {});
      const ordenados = [...(listaResp || [])].sort(
        (a, b) => (b.id || 0) - (a.id || 0)
      );
      setLancamentosMes(ordenados);
    } catch {
      // silencioso
    } finally {
      setCarregando(false);
      setAtualizando(false);
    }
  }, [mes, ano]);

  useEffect(() => {
    setCarregando(true);
    setCategoriaFiltro(null);
    carregarDados();
  }, [carregarDados]);

  const alterarMes = (delta: number) => {
    let novoMes = mes + delta;
    let novoAno = ano;
    if (novoMes < 1) {
      novoMes = 12;
      novoAno -= 1;
    } else if (novoMes > 12) {
      novoMes = 1;
      novoAno += 1;
    }
    setMes(novoMes);
    setAno(novoAno);
  };

  const handleSalvarSaldo = async () => {
    const valorNum = parseFloat(novoSaldoInput.replace(",", "."));
    if (isNaN(valorNum)) return;
    setSalvandoSaldo(true);
    try {
      await apiFinancas.atualizarSaldo(valorNum);
      if (onSaldoAtualizado) await onSaldoAtualizado();
      setModalSaldoVisivel(false);
    } finally {
      setSalvandoSaldo(false);
    }
  };

  const listaCategorias = Object.entries(categorias).sort(
    (a, b) => b[1] - a[1]
  );

  const lancamentosFiltrados = lancamentosMes.filter((item) => {
    if (categoriaFiltro && item.categoria !== categoriaFiltro) return false;
    if (buscaDataOuTexto.trim()) {
      const termo = buscaDataOuTexto.trim().toLowerCase();
      const matchDesc = (item.descricao || "").toLowerCase().includes(termo);
      const matchData = (item.data || "").toLowerCase().includes(termo);
      const matchCat = (item.categoria || "").toLowerCase().includes(termo);
      return matchDesc || matchData || matchCat;
    }
    return true;
  });

  return (
    <ScrollView
      style={estilos.container}
      contentContainerStyle={estilos.conteudo}
      keyboardShouldPersistTaps="handled"
      refreshControl={
        <RefreshControl
          refreshing={atualizando}
          onRefresh={() => {
            setAtualizando(true);
            carregarDados();
          }}
          tintColor={CORES.verde}
        />
      }
    >
      {/* Topo Limpo Estilo Spotify / Revolut */}
      <View style={estilos.topoSaldo}>
        <View style={estilos.linhaMes}>
          <Pressable
            style={estilos.saldoTituloRow}
            onPress={() => {
              setNovoSaldoInput(String(usuario?.saldo ?? 0));
              setModalSaldoVisivel(true);
            }}
          >
            <Text style={estilos.labelTopo}>Saldo atual</Text>
            <Ionicons
              name="pencil-outline"
              size={13}
              color={CORES.textoSecundario}
            />
          </Pressable>

          <View style={estilos.pilulaMes}>
            <Pressable onPress={() => alterarMes(-1)} hitSlop={8}>
              <Ionicons name="chevron-back" size={16} color="#FFFFFF" />
            </Pressable>
            <Text style={estilos.textoMes}>
              {NOMES_MESES[mes - 1]} {ano}
            </Text>
            <Pressable onPress={() => alterarMes(1)} hitSlop={8}>
              <Ionicons name="chevron-forward" size={16} color="#FFFFFF" />
            </Pressable>
          </View>
        </View>

        <Pressable
          onPress={() => {
            setNovoSaldoInput(String(usuario?.saldo ?? 0));
            setModalSaldoVisivel(true);
          }}
        >
          <Text style={estilos.valorPrincipal}>
            {formatarMoeda(usuario?.saldo ?? 0)}
          </Text>
        </Pressable>

        <View style={estilos.resumoRapidoRow}>
          <Text style={estilos.textoSaidas}>
            Entradas:{" "}
            <Text style={{ color: CORES.verde, fontWeight: "700" }}>
              +{formatarMoeda(ganhoTotal)}
            </Text>
            {"  •  "}
            Saídas:{" "}
            <Text style={{ color: CORES.dourado, fontWeight: "700" }}>
              -{formatarMoeda(gastoTotal)}
            </Text>
          </Text>
        </View>
      </View>

      {carregando ? (
        <View style={{ paddingVertical: 50, alignItems: "center" }}>
          <ActivityIndicator size="large" color={CORES.verde} />
        </View>
      ) : (
        <>
          {/* Categorias em Pílulas Horizontais Interativas (toque para filtrar por categoria!) */}
          {listaCategorias.length > 0 ? (
            <View style={estilos.secao}>
              <View style={estilos.cabecalhoSecaoRow}>
                <Text style={estilos.tituloSecao}>Categorias</Text>
                {categoriaFiltro ? (
                  <Pressable onPress={() => setCategoriaFiltro(null)}>
                    <Text style={estilos.limparFiltro}>Mostrar todas</Text>
                  </Pressable>
                ) : null}
              </View>
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={{ gap: 10 }}
              >
                {listaCategorias.map(([cat, valorCat], idx) => {
                  const pct =
                    gastoTotal > 0
                      ? Math.round((valorCat / gastoTotal) * 100)
                      : 0;
                  const selecionada = categoriaFiltro === cat;
                  return (
                    <Pressable
                      key={cat}
                      style={[
                        estilos.cardCategoria,
                        selecionada && estilos.cardCategoriaAtiva,
                      ]}
                      onPress={() =>
                        setCategoriaFiltro(selecionada ? null : cat)
                      }
                    >
                      <View style={estilos.topoCardCat}>
                        <Ionicons
                          name={iconePorCategoria(cat) as any}
                          size={18}
                          color={
                            selecionada
                              ? "#04131E"
                              : idx === 0
                              ? CORES.dourado
                              : CORES.verde
                          }
                        />
                        <Text
                          style={[
                            estilos.pctCat,
                            selecionada && { color: "#04131E" },
                          ]}
                        >
                          {pct}%
                        </Text>
                      </View>
                      <Text
                        style={[
                          estilos.nomeCat,
                          selecionada && { color: "#04131E" },
                        ]}
                        numberOfLines={1}
                      >
                        {cat}
                      </Text>
                      <Text
                        style={[
                          estilos.valorCat,
                          selecionada && { color: "#04131E" },
                        ]}
                      >
                        {formatarMoeda(valorCat)}
                      </Text>
                    </Pressable>
                  );
                })}
              </ScrollView>
            </View>
          ) : null}

          {/* Busca / Filtro por Data Específica ou Descrição */}
          <View style={estilos.secao}>
            <Text style={estilos.tituloSecao}>Atividade</Text>

            <View style={estilos.barraBusca}>
              <Ionicons
                name="search-outline"
                size={18}
                color={CORES.textoSecundario}
              />
              <TextInput
                style={estilos.inputBusca}
                placeholder="Filtrar por data (ex: 2026-11-10) ou nome..."
                placeholderTextColor={CORES.textoSecundario}
                value={buscaDataOuTexto}
                onChangeText={setBuscaDataOuTexto}
              />
              {buscaDataOuTexto ? (
                <Pressable onPress={() => setBuscaDataOuTexto("")}>
                  <Ionicons
                    name="close-circle"
                    size={18}
                    color={CORES.textoSecundario}
                  />
                </Pressable>
              ) : null}
            </View>

            {lancamentosFiltrados.length === 0 ? (
              <Text style={estilos.textoVazio}>
                Nenhum lançamento encontrado para este filtro.
              </Text>
            ) : (
              lancamentosFiltrados.map((item) => (
                <Pressable
                  key={item.id || item.numero_usuario}
                  style={estilos.itemTransacao}
                  onPress={() => onEditarTransacao(item)}
                >
                  <View style={estilos.circuloAvatar}>
                    <Ionicons
                      name={
                        item.tipo === "GANHO"
                          ? "trending-up"
                          : (iconePorCategoria(item.categoria) as any)
                      }
                      size={20}
                      color={item.tipo === "GANHO" ? CORES.verde : "#FFFFFF"}
                    />
                  </View>

                  <View style={{ flex: 1 }}>
                    <Text style={estilos.nomeTransacao} numberOfLines={1}>
                      {item.descricao}
                    </Text>
                    <Text style={estilos.subTransacao}>
                      {item.tipo === "GANHO" ? "Entrada" : item.categoria} •{" "}
                      {item.data}
                    </Text>
                  </View>

                  <View style={estilos.direitaTransacao}>
                    <Text
                      style={[
                        estilos.valorTransacao,
                        item.tipo === "GANHO" && { color: CORES.verde },
                      ]}
                    >
                      {item.tipo === "GANHO" ? "+" : "-"}
                      {formatarMoeda(item.valor)}
                    </Text>
                    <Pressable
                      onPress={async () => {
                        await onExcluirTransacao(item.numero_usuario);
                        carregarDados();
                      }}
                      hitSlop={10}
                    >
                      <Ionicons
                        name="trash-outline"
                        size={15}
                        color={CORES.textoSecundario}
                      />
                    </Pressable>
                  </View>
                </Pressable>
              ))
            )}
          </View>
        </>
      )}

      {/* Modal de Atualização Rápida de Saldo (PUT /saldo) */}
      <Modal visible={modalSaldoVisivel} transparent animationType="fade">
        <Pressable
          style={estilos.modalOverlay}
          onPress={() => setModalSaldoVisivel(false)}
        >
          <Pressable
            style={estilos.modalSheet}
            onPress={(e) => e.stopPropagation()}
          >
            <Text style={estilos.modalTitulo}>Atualizar saldo atual</Text>
            <TextInput
              style={estilos.modalInput}
              keyboardType="decimal-pad"
              value={novoSaldoInput}
              onChangeText={setNovoSaldoInput}
              placeholder="0.00"
              placeholderTextColor={CORES.textoSecundario}
              autoFocus
            />
            <Pressable
              style={estilos.modalBotao}
              onPress={handleSalvarSaldo}
              disabled={salvandoSaldo}
            >
              {salvandoSaldo ? (
                <ActivityIndicator color="#04131E" />
              ) : (
                <Text style={estilos.modalBotaoTexto}>Salvar saldo</Text>
              )}
            </Pressable>
          </Pressable>
        </Pressable>
      </Modal>
    </ScrollView>
  );
}

const estilos = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: CORES.fundo,
  },
  conteudo: {
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 40,
  },
  topoSaldo: {
    marginBottom: 28,
  },
  linhaMes: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  saldoTituloRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  labelTopo: {
    color: CORES.textoSecundario,
    fontSize: 14,
    fontWeight: "600",
  },
  pilulaMes: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    backgroundColor: CORES.fundoElevado,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  textoMes: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "700",
  },
  valorPrincipal: {
    color: "#FFFFFF",
    fontSize: 38,
    fontWeight: "800",
    letterSpacing: -1,
    marginTop: 4,
  },
  resumoRapidoRow: {
    marginTop: 6,
  },
  textoSaidas: {
    color: CORES.textoSecundario,
    fontSize: 14,
  },
  secao: {
    marginBottom: 28,
  },
  cabecalhoSecaoRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 14,
  },
  tituloSecao: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "700",
    marginBottom: 12,
    letterSpacing: -0.3,
  },
  limparFiltro: {
    color: CORES.verde,
    fontSize: 13,
    fontWeight: "600",
    marginBottom: 12,
  },
  cardCategoria: {
    width: 135,
    backgroundColor: CORES.fundoElevado,
    borderRadius: 16,
    padding: 14,
    justifyContent: "space-between",
    height: 110,
  },
  cardCategoriaAtiva: {
    backgroundColor: CORES.verde,
  },
  topoCardCat: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  pctCat: {
    color: CORES.textoSecundario,
    fontSize: 12,
    fontWeight: "700",
  },
  nomeCat: {
    color: CORES.textoSecundario,
    fontSize: 13,
    fontWeight: "600",
    marginTop: 8,
  },
  valorCat: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "700",
  },
  barraBusca: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: CORES.fundoElevado,
    borderRadius: 12,
    paddingHorizontal: 14,
    height: 44,
    gap: 10,
    marginBottom: 14,
  },
  inputBusca: {
    flex: 1,
    color: "#FFFFFF",
    fontSize: 14,
    height: "100%",
  },
  textoVazio: {
    color: CORES.textoSecundario,
    fontSize: 14,
    marginTop: 6,
  },
  itemTransacao: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 12,
    gap: 14,
  },
  circuloAvatar: {
    width: 46,
    height: 46,
    borderRadius: 23,
    backgroundColor: CORES.fundoElevado,
    alignItems: "center",
    justifyContent: "center",
  },
  nomeTransacao: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "600",
  },
  subTransacao: {
    color: CORES.textoSecundario,
    fontSize: 13,
    marginTop: 2,
  },
  direitaTransacao: {
    alignItems: "flex-end",
    gap: 4,
  },
  valorTransacao: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "700",
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.65)",
    justifyContent: "center",
    padding: 24,
  },
  modalSheet: {
    backgroundColor: CORES.fundoElevado,
    borderRadius: 20,
    padding: 22,
    gap: 14,
  },
  modalTitulo: {
    color: "#FFFFFF",
    fontSize: 17,
    fontWeight: "700",
  },
  modalInput: {
    height: 50,
    backgroundColor: CORES.superficieInput,
    borderRadius: 10,
    paddingHorizontal: 16,
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "700",
  },
  modalBotao: {
    height: 48,
    borderRadius: 24,
    backgroundColor: CORES.verde,
    alignItems: "center",
    justifyContent: "center",
  },
  modalBotaoTexto: {
    color: "#04131E",
    fontSize: 15,
    fontWeight: "700",
  },
});

import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Modal,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { DadosTransacaoCard } from "../types/api";
import { CORES } from "../theme/colors";

interface Props {
  visivel: boolean;
  transacao: DadosTransacaoCard | null;
  onFechar: () => void;
  onSalvar: (
    numeroUsuario: number,
    dados: {
      valor: number;
      categoria: string;
      descricao: string;
      tipo: string;
      data: string;
    }
  ) => Promise<void>;
}

const CATEGORIAS = [
  "Alimentação",
  "Transporte",
  "Moradia",
  "Saúde",
  "Lazer",
  "Educação",
  "Outros",
];

export function ModalEditarTransacao({
  visivel,
  transacao,
  onFechar,
  onSalvar,
}: Props) {
  const [descricao, setDescricao] = useState("");
  const [valor, setValor] = useState("");
  const [categoria, setCategoria] = useState("Outros");
  const [data, setData] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    if (transacao) {
      setDescricao(transacao.descricao || "");
      setValor(String(transacao.valor ?? ""));
      setCategoria(transacao.categoria || "Outros");
      setData(transacao.data || "");
      setErro(null);
    }
  }, [transacao]);

  if (!transacao) return null;

  const handleConfirmar = async () => {
    const valorNumerico = parseFloat(valor.replace(",", "."));
    if (!descricao.trim() || isNaN(valorNumerico) || valorNumerico <= 0) {
      setErro("Preencha descrição e valor.");
      return;
    }

    setSalvando(true);
    setErro(null);
    try {
      await onSalvar(transacao.numero_usuario, {
        descricao: descricao.trim(),
        valor: valorNumerico,
        categoria,
        tipo: transacao.tipo || "GASTO",
        data: data.trim(),
      });
      onFechar();
    } catch (e: any) {
      setErro(e?.message || "Erro ao salvar.");
    } finally {
      setSalvando(false);
    }
  };

  return (
    <Modal visible={visivel} transparent animationType="slide">
      <Pressable style={estilos.overlay} onPress={onFechar}>
        <Pressable style={estilos.sheet} onPress={(e) => e.stopPropagation()}>
          <View style={estilos.barraArraste} />
          <Text style={estilos.titulo}>Editar lançamento</Text>

          {erro ? <Text style={estilos.erro}>{erro}</Text> : null}

          <TextInput
            style={estilos.input}
            value={descricao}
            onChangeText={setDescricao}
            placeholder="Descrição"
            placeholderTextColor={CORES.textoSecundario}
          />

          <TextInput
            style={estilos.input}
            value={valor}
            onChangeText={setValor}
            keyboardType="decimal-pad"
            placeholder="Valor (R$)"
            placeholderTextColor={CORES.textoSecundario}
          />

          <View style={estilos.chipsCategorias}>
            {CATEGORIAS.map((cat) => (
              <Pressable
                key={cat}
                onPress={() => setCategoria(cat)}
                style={[
                  estilos.chip,
                  categoria === cat && estilos.chipSelecionado,
                ]}
              >
                <Text
                  style={[
                    estilos.textoChip,
                    categoria === cat && estilos.textoChipSelecionado,
                  ]}
                >
                  {cat}
                </Text>
              </Pressable>
            ))}
          </View>

          <Pressable
            style={estilos.botaoSalvar}
            onPress={handleConfirmar}
            disabled={salvando}
          >
            {salvando ? (
              <ActivityIndicator color="#04131E" />
            ) : (
              <Text style={estilos.textoSalvar}>Salvar</Text>
            )}
          </Pressable>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const estilos = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.65)",
    justifyContent: "flex-end",
  },
  sheet: {
    backgroundColor: CORES.fundoElevado,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    paddingBottom: 38,
    gap: 12,
  },
  barraArraste: {
    width: 38,
    height: 4,
    borderRadius: 2,
    backgroundColor: CORES.bordaInput,
    alignSelf: "center",
    marginBottom: 8,
  },
  titulo: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "700",
    marginBottom: 4,
  },
  erro: {
    color: CORES.perigo,
    fontSize: 13,
  },
  input: {
    height: 50,
    backgroundColor: CORES.superficieInput,
    color: "#FFFFFF",
    borderRadius: 10,
    paddingHorizontal: 16,
    fontSize: 15,
  },
  chipsCategorias: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginVertical: 4,
  },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: CORES.superficieInput,
  },
  chipSelecionado: {
    backgroundColor: CORES.verde,
  },
  textoChip: {
    color: CORES.textoSecundario,
    fontSize: 13,
    fontWeight: "600",
  },
  textoChipSelecionado: {
    color: "#04131E",
    fontWeight: "700",
  },
  botaoSalvar: {
    height: 50,
    borderRadius: 25,
    backgroundColor: CORES.verde,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 8,
  },
  textoSalvar: {
    color: "#04131E",
    fontSize: 16,
    fontWeight: "700",
  },
});

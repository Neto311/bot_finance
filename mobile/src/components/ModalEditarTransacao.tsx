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
      setErro("Informe uma descrição e um valor válido.");
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
      setErro(e?.message || "Erro ao salvar alterações.");
    } finally {
      setSalvando(false);
    }
  };

  return (
    <Modal visible={visivel} transparent animationType="fade">
      <View style={estilos.overlay}>
        <View style={estilos.modalCard}>
          <Text style={estilos.titulo}>
            Editar Lançamento #{transacao.numero_usuario}
          </Text>

          {erro ? <Text style={estilos.erro}>{erro}</Text> : null}

          <Text style={estilos.label}>Descrição</Text>
          <TextInput
            style={estilos.input}
            value={descricao}
            onChangeText={setDescricao}
            placeholder="Descrição"
            placeholderTextColor="#64748b"
          />

          <Text style={estilos.label}>Valor (R$)</Text>
          <TextInput
            style={estilos.input}
            value={valor}
            onChangeText={setValor}
            keyboardType="decimal-pad"
            placeholder="0.00"
            placeholderTextColor="#64748b"
          />

          <Text style={estilos.label}>Categoria</Text>
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

          <Text style={estilos.label}>Data (AAAA-MM-DD)</Text>
          <TextInput
            style={estilos.input}
            value={data}
            onChangeText={setData}
            placeholder="2026-11-10"
            placeholderTextColor="#64748b"
          />

          <View style={estilos.botoes}>
            <Pressable style={estilos.botaoCancelar} onPress={onFechar}>
              <Text style={estilos.textoCancelar}>Cancelar</Text>
            </Pressable>

            <Pressable
              style={estilos.botaoSalvar}
              onPress={handleConfirmar}
              disabled={salvando}
            >
              {salvando ? (
                <ActivityIndicator color="#042f2e" />
              ) : (
                <Text style={estilos.textoSalvar}>Salvar</Text>
              )}
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const estilos = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.65)",
    justifyContent: "center",
    padding: 20,
  },
  modalCard: {
    backgroundColor: "#111b21",
    borderRadius: 18,
    padding: 20,
    borderWidth: 1,
    borderColor: "#2a3942",
    maxWidth: 440,
    width: "100%",
    alignSelf: "center",
  },
  titulo: {
    color: "#f8fafc",
    fontSize: 18,
    fontWeight: "700",
    marginBottom: 10,
  },
  erro: {
    color: "#fca5a5",
    fontSize: 13,
    marginBottom: 8,
  },
  label: {
    color: "#cbd5e1",
    fontSize: 12,
    fontWeight: "600",
    marginTop: 10,
    marginBottom: 4,
  },
  input: {
    backgroundColor: "#202c33",
    color: "#f8fafc",
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    borderWidth: 1,
    borderColor: "#2a3942",
  },
  chipsCategorias: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
    marginTop: 4,
  },
  chip: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 14,
    backgroundColor: "#202c33",
    borderWidth: 1,
    borderColor: "#2a3942",
  },
  chipSelecionado: {
    backgroundColor: "rgba(16, 185, 129, 0.2)",
    borderColor: "#10b981",
  },
  textoChip: {
    color: "#94a3b8",
    fontSize: 12,
  },
  textoChipSelecionado: {
    color: "#34d399",
    fontWeight: "700",
  },
  botoes: {
    flexDirection: "row",
    justifyContent: "flex-end",
    gap: 10,
    marginTop: 20,
  },
  botaoCancelar: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: "#202c33",
  },
  textoCancelar: {
    color: "#cbd5e1",
    fontWeight: "600",
  },
  botaoSalvar: {
    paddingHorizontal: 18,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: "#10b981",
  },
  textoSalvar: {
    color: "#042f2e",
    fontWeight: "700",
  },
});

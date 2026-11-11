import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";

const CHAVE_ACCESS_TOKEN = "bot_financa_access_token";
const CHAVE_REFRESH_TOKEN = "bot_financa_refresh_token";

async function salvarItem(chave: string, valor: string): Promise<void> {
  if (Platform.OS === "web") {
    if (typeof window !== "undefined" && window.localStorage) {
      window.localStorage.setItem(chave, valor);
    }
    return;
  }
  await SecureStore.setItemAsync(chave, valor);
}

async function obterItem(chave: string): Promise<string | null> {
  if (Platform.OS === "web") {
    if (typeof window !== "undefined" && window.localStorage) {
      return window.localStorage.getItem(chave);
    }
    return null;
  }
  return await SecureStore.getItemAsync(chave);
}

async function removerItem(chave: string): Promise<void> {
  if (Platform.OS === "web") {
    if (typeof window !== "undefined" && window.localStorage) {
      window.localStorage.removeItem(chave);
    }
    return;
  }
  await SecureStore.deleteItemAsync(chave);
}

export async function salvarTokens(
  accessToken: string,
  refreshToken: string
): Promise<void> {
  await salvarItem(CHAVE_ACCESS_TOKEN, accessToken);
  await salvarItem(CHAVE_REFRESH_TOKEN, refreshToken);
}

export async function obterAccessToken(): Promise<string | null> {
  return await obterItem(CHAVE_ACCESS_TOKEN);
}

export async function obterRefreshToken(): Promise<string | null> {
  return await obterItem(CHAVE_REFRESH_TOKEN);
}

export async function limparTokens(): Promise<void> {
  await removerItem(CHAVE_ACCESS_TOKEN);
  await removerItem(CHAVE_REFRESH_TOKEN);
}

/**
 * API clients index
 * Centralized exports for all API modules
 */
export * from './auth';
export * from './clientes';
export * from './solicitacoes';
export * from './documentos';
export { default as api } from './axiosInstance';

// Backward compatibility - export with old names
import { authApi } from './auth';
import { clientesApi } from './clientes';
import { solicitacoesApi } from './solicitacoes';

export const authAPI = authApi;
export const clientesAPI = clientesApi;
export const solicitacoesAPI = solicitacoesApi;

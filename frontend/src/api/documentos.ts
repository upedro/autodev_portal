/**
 * Documentos API client
 */
import api from './axiosInstance';

export interface Documento {
  filename: string;
  size_bytes: number;
  download_url: string;
  expires_in_hours: number;
  last_modified?: string;
}

export interface CNJDocumentos {
  cnj: string;
  total_documentos: number;
  documentos: Documento[];
}

export interface DocumentosResponse {
  solicitacao_id: string;
  status: string;
  cliente_nome: string;
  total_cnjs_com_documentos: number;
  cnjs: CNJDocumentos[];
}

export const documentosApi = {
  /**
   * Get all documents for a solicitacao
   */
  async getBySolicitacao(solicitacaoId: string): Promise<DocumentosResponse> {
    const response = await api.get<DocumentosResponse>(`/documentos/${solicitacaoId}`);
    return response.data;
  },

  /**
   * Get documents for a specific CNJ in a solicitacao
   */
  async getByCNJ(solicitacaoId: string, cnj: string): Promise<CNJDocumentos> {
    const response = await api.get<CNJDocumentos>(`/documentos/${solicitacaoId}/${cnj}`);
    return response.data;
  },

  /**
   * Download a document directly (opens in new tab)
   */
  downloadDocument(url: string): void {
    window.open(url, '_blank');
  },
};

/**
 * Solicitações API client
 */
import api from './axiosInstance';

export interface ResultadoProcessamento {
  cnj: string;
  status: string;
  documentos_encontrados: number;
  documentos_urls: string[];
  erro?: string;
  processado_em?: string;
}

export interface Solicitacao {
  id: string;
  user_id: string;
  cliente_id: string;
  cliente_nome?: string;
  servico: string;
  cnjs: string[];
  status: string;
  total_cnjs: number;
  cnjs_processados: number;
  cnjs_sucesso: number;
  cnjs_erro: number;
  resultados: ResultadoProcessamento[];
  created_at: string;
  updated_at: string;
  iniciado_em?: string;
  concluido_em?: string;
}

export interface CreateSolicitacaoDto {
  cliente_id: string;
  servico: string;
  cnjs: string[];
}

export const solicitacoesApi = {
  /**
   * List user's solicitacoes
   */
  async list(params?: {
    skip?: number;
    limit?: number;
    status?: string;
  }): Promise<Solicitacao[]> {
    const response = await api.get<Solicitacao[]>('/solicitacoes', { params });
    return response.data;
  },

  /**
   * Get solicitacao by ID
   */
  async getById(id: string): Promise<Solicitacao> {
    const response = await api.get<Solicitacao>(`/solicitacoes/${id}`);
    return response.data;
  },

  /**
   * Create new solicitacao
   */
  async create(data: CreateSolicitacaoDto): Promise<Solicitacao> {
    const response = await api.post<Solicitacao>('/solicitacoes', data);
    return response.data;
  },

  /**
   * Create solicitacao from Excel upload
   */
  async createFromExcel(
    file: File,
    clienteId: string,
    servico: string = 'buscar_documentos'
  ): Promise<Solicitacao> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('cliente_id', clienteId);
    formData.append('servico', servico);

    const response = await api.post<Solicitacao>('/solicitacoes/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

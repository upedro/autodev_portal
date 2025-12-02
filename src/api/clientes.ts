/**
 * Clients API client
 */
import api from './axiosInstance';

export interface Cliente {
  id: string;
  nome: string;
  codigo: string;
  ativo: boolean;
  descricao?: string;
  created_at: string;
}

export const clientesApi = {
  /**
   * List all active clients
   */
  async list(ativoApenas: boolean = true): Promise<Cliente[]> {
    const response = await api.get<Cliente[]>('/clientes', {
      params: { ativo_apenas: ativoApenas },
    });
    return response.data;
  },

  /**
   * Get client by ID
   */
  async getById(id: string): Promise<Cliente> {
    const response = await api.get<Cliente>(`/clientes/${id}`);
    return response.data;
  },
};

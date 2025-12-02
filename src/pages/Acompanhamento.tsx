import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { TableSolicitacoes } from '../components/TableSolicitacoes';
import { Solicitacao, solicitacoesAPI, clientesAPI, Cliente } from '../api';
import { Label } from '../components/ui/label';
import { toast } from 'sonner@2.0.3';

export function Acompanhamento() {
  const [solicitacoes, setSolicitacoes] = useState<Solicitacao[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [clienteFilter, setClienteFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const loadData = async () => {
    setLoading(true);
    try {
      const [solicitacoesData, clientesData] = await Promise.all([
        solicitacoesAPI.list(),
        clientesAPI.list(),
      ]);
      setSolicitacoes(solicitacoesData);
      setClientes(clientesData);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    // Atualização automática a cada 15 segundos
    const interval = setInterval(() => {
      loadData();
    }, 15000);

    return () => clearInterval(interval);
  }, []);

  const filteredSolicitacoes = solicitacoes.filter((s) => {
    if (clienteFilter !== 'all' && s.cliente_id !== clienteFilter) return false;
    if (statusFilter !== 'all' && s.status !== statusFilter) return false;
    return true;
  });

  const handleDownload = async (id: string) => {
    try {
      const blob = await solicitacoesAPI.download(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `resultado-${id}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Download iniciado com sucesso!');
    } catch (error) {
      toast.error('Erro ao fazer download');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl text-[#0d0d16]">Acompanhamento de Demandas</h1>
        <p className="text-gray-600 mt-1">
          Monitore o progresso de todas as suas automações RPA em tempo real
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
          <CardDescription>
            Filtre as solicitações por cliente e status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="cliente-filter">Cliente</Label>
              <Select value={clienteFilter} onValueChange={setClienteFilter}>
                <SelectTrigger id="cliente-filter">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos os clientes</SelectItem>
                  {clientes.map((cliente) => (
                    <SelectItem key={cliente.id} value={cliente.id}>
                      {cliente.nome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="status-filter">Status</Label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger id="status-filter">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos os status</SelectItem>
                  <SelectItem value="pendente">Pendente</SelectItem>
                  <SelectItem value="processando">Processando</SelectItem>
                  <SelectItem value="concluido">Concluído</SelectItem>
                  <SelectItem value="erro">Erro</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Todas as Solicitações</CardTitle>
          <CardDescription>
            Atualizações automáticas a cada 15 segundos
          </CardDescription>
        </CardHeader>
        <CardContent>
          <TableSolicitacoes
            solicitacoes={filteredSolicitacoes}
            loading={loading}
            onRefresh={loadData}
            onDownload={handleDownload}
          />
        </CardContent>
      </Card>
    </div>
  );
}

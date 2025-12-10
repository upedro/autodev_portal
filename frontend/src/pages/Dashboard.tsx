import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { TableSolicitacoes } from '../components/TableSolicitacoes';
import { Solicitacao, solicitacoesAPI } from '../api';
import { Plus, FileText, TrendingUp, Clock } from 'lucide-react';
import { Skeleton } from '../components/ui/skeleton';
import { toast } from 'sonner@2.0.3';

export function Dashboard() {
  const [solicitacoes, setSolicitacoes] = useState<Solicitacao[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const loadSolicitacoes = async () => {
    setLoading(true);
    try {
      const data = await solicitacoesAPI.list();
      setSolicitacoes(data);
    } catch (error) {
      toast.error('Erro ao carregar solicitações');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSolicitacoes();
  }, []);

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

  const stats = {
    total: solicitacoes.length,
    concluidas: solicitacoes.filter(s => s.status === 'concluido').length,
    pendentes: solicitacoes.filter(s => s.status === 'pendente' || s.status === 'processando').length,
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl text-[#0d0d16]">Minhas Solicitações RPA</h1>
          <p className="text-gray-600 mt-1">
            Gerencie suas demandas de automação para processos jurídicos
          </p>
        </div>
        <Button onClick={() => navigate('/solicitar')} size="lg" className="bg-[#3ecf8e] hover:bg-[#35b87d] text-[#0d0d16]">
          <Plus className="mr-2 h-5 w-5" />
          Nova Solicitação
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">Total de Solicitações</CardTitle>
            <FileText className="h-4 w-4 text-gray-600" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl">{stats.total}</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">Concluídas</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl text-green-600">{stats.concluidas}</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">Em Andamento</CardTitle>
            <Clock className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl text-yellow-600">{stats.pendentes}</div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Solicitações Recentes</CardTitle>
          <CardDescription>
            Visualize o histórico e status das suas solicitações
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : (
            <TableSolicitacoes
              solicitacoes={solicitacoes.slice(0, 5)}
              onRefresh={loadSolicitacoes}
              onDownload={handleDownload}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

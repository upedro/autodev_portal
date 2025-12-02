import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { ProcessoStatusCard } from '../components/ProcessoStatusCard';
import { StatusTag } from '../components/StatusTag';
import { Skeleton } from '../components/ui/skeleton';
import { Solicitacao, solicitacoesAPI } from '../api';
import { ArrowLeft, Download, RefreshCw, Calendar, Building2, Briefcase } from 'lucide-react';
import { toast } from 'sonner@2.0.3';
import { Progress } from '../components/ui/progress';
import { Separator } from '../components/ui/separator';

export function DetalheSolicitacao() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [solicitacao, setSolicitacao] = useState<Solicitacao | null>(null);
  const [loading, setLoading] = useState(true);

  const loadSolicitacao = async () => {
    if (!id) return;
    
    setLoading(true);
    try {
      const data = await solicitacoesAPI.getById(id);
      if (!data) {
        toast.error('Solicitação não encontrada');
        navigate('/dashboard');
        return;
      }
      setSolicitacao(data);
    } catch (error) {
      toast.error('Erro ao carregar solicitação');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSolicitacao();
    
    // Auto-refresh a cada 10 segundos se houver processos em andamento
    const interval = setInterval(() => {
      if (solicitacao?.status === 'em_execucao' || solicitacao?.status === 'pendente') {
        loadSolicitacao();
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [id]);

  const handleDownload = async () => {
    if (!id) return;
    
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

  const formatDate = (isoDate: string) => {
    const date = new Date(isoDate);
    return new Intl.DateTimeFormat('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  const getProgress = () => {
    if (!solicitacao) return 0;
    if (solicitacao.total_cnjs === 0) return 0;
    return (solicitacao.cnjs_processados / solicitacao.total_cnjs) * 100;
  };

  const getStatusCounts = () => {
    if (!solicitacao) return { concluido: 0, processando: 0, pendente: 0, erro: 0 };
    return {
      concluido: solicitacao.cnjs_sucesso,
      processando: solicitacao.status === 'em_execucao' ?
        solicitacao.total_cnjs - solicitacao.cnjs_processados : 0,
      pendente: solicitacao.status === 'pendente' ? solicitacao.total_cnjs : 0,
      erro: solicitacao.cnjs_erro,
    };
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  if (!solicitacao) {
    return null;
  }

  const statusCounts = getStatusCounts();
  const progress = getProgress();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/acompanhamento')}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Voltar
          </Button>
          <div>
            <h1 className="text-3xl text-[#0d0d16]">Detalhes da Demanda</h1>
            <p className="text-gray-600 mt-1">ID: #{solicitacao.id}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={loadSolicitacao}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
          {solicitacao.status === 'concluido' && (
            <Button onClick={handleDownload} className="bg-[#3ecf8e] hover:bg-[#35b87d] text-[#0d0d16]">
              <Download className="h-4 w-4 mr-2" />
              Baixar Resultado
            </Button>
          )}
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle>Informações Gerais</CardTitle>
              <CardDescription>Dados da demanda RPA e progresso geral</CardDescription>
            </div>
            <StatusTag status={solicitacao.status} />
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="flex items-start gap-3">
              <Building2 className="h-5 w-5 text-gray-600 mt-0.5" />
              <div>
                <p className="text-sm text-gray-600">Cliente</p>
                <p className="mt-1">{solicitacao.cliente_nome}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Briefcase className="h-5 w-5 text-gray-600 mt-0.5" />
              <div>
                <p className="text-sm text-gray-600">Serviço</p>
                <p className="mt-1">{solicitacao.servico}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Calendar className="h-5 w-5 text-gray-600 mt-0.5" />
              <div>
                <p className="text-sm text-gray-600">Data de Criação</p>
                <p className="mt-1">{formatDate(solicitacao.created_at)}</p>
              </div>
            </div>
          </div>

          <Separator />

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-sm">Progresso Geral</p>
              <p className="text-sm text-gray-600">
                {statusCounts.concluido} de {solicitacao.total_cnjs} processos concluídos
              </p>
            </div>
            <Progress value={progress} className="h-2" />
          </div>

          <div className="grid gap-3 md:grid-cols-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <p className="text-sm">
                <span className="font-medium">{statusCounts.concluido}</span> Concluído
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500" />
              <p className="text-sm">
                <span className="font-medium">{statusCounts.processando}</span> Processando
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-yellow-500" />
              <p className="text-sm">
                <span className="font-medium">{statusCounts.pendente}</span> Pendente
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <p className="text-sm">
                <span className="font-medium">{statusCounts.erro}</span> Erro
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Status Individual dos Processos</CardTitle>
          <CardDescription>
            Acompanhe o status de cada número CNJ separadamente
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            {solicitacao.resultados && solicitacao.resultados.length > 0 ? (
              solicitacao.resultados.map((resultado) => (
                <ProcessoStatusCard key={resultado.cnj} processo={resultado} />
              ))
            ) : (
              <div className="col-span-2 text-center py-8 text-gray-500">
                <p>Aguardando processamento...</p>
                <p className="text-sm mt-2">Os CNJs serão processados em breve pelo sistema RPA</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

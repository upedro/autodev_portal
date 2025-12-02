import { Card, CardContent, CardHeader } from './ui/card';
import { StatusTag } from './StatusTag';
import { ResultadoProcessamento } from '../api';
import { FileText, AlertCircle, CheckCircle2, Clock } from 'lucide-react';
import { Badge } from './ui/badge';

interface ProcessoStatusCardProps {
  processo: ResultadoProcessamento;
}

export function ProcessoStatusCard({ processo }: ProcessoStatusCardProps) {
  const formatDate = (isoDate: string | undefined) => {
    if (!isoDate) return 'Aguardando...';
    const date = new Date(isoDate);
    if (isNaN(date.getTime())) return 'Data inválida';
    return new Intl.DateTimeFormat('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  const getIcon = () => {
    switch (processo.status) {
      case 'concluido':
        return <CheckCircle2 className="h-5 w-5 text-green-600" />;
      case 'erro':
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      case 'processando':
        return <Clock className="h-5 w-5 text-blue-600 animate-spin" />;
      default:
        return <FileText className="h-5 w-5 text-yellow-600" />;
    }
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            {getIcon()}
            <div>
              <p className="font-mono text-sm">{processo.cnj}</p>
              <p className="text-xs text-gray-500 mt-0.5">
                {processo.processado_em ? `Processado em ${formatDate(processo.processado_em)}` : 'Aguardando processamento'}
              </p>
            </div>
          </div>
          <StatusTag status={processo.status} />
        </div>
      </CardHeader>
      <CardContent>
        {processo.erro && (
          <p className="text-sm text-red-600 mb-3">{processo.erro}</p>
        )}
        {processo.documentos_encontrados > 0 && (
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="bg-green-50 text-green-700">
              <FileText className="h-3 w-3 mr-1" />
              {processo.documentos_encontrados} {processo.documentos_encontrados === 1 ? 'documento' : 'documentos'}
            </Badge>
          </div>
        )}
        {!processo.processado_em && (
          <p className="text-sm text-gray-500">Aguardando processamento pelo RPA...</p>
        )}
      </CardContent>
    </Card>
  );
}

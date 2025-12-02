import { Badge } from './ui/badge';
import { CheckCircle2, Clock, AlertCircle, Loader2 } from 'lucide-react';

type Status = 'pendente' | 'processando' | 'concluido' | 'erro' | 'pending' | 'processing' | 'completed' | 'failed' | 'em_execucao';

interface StatusTagProps {
  status: string;
}

const statusConfig: Record<string, {
  label: string;
  variant: 'secondary' | 'destructive';
  icon: any;
  className: string;
}> = {
  pendente: {
    label: 'Pendente',
    variant: 'secondary' as const,
    icon: Clock,
    className: 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100',
  },
  pending: {
    label: 'Pendente',
    variant: 'secondary' as const,
    icon: Clock,
    className: 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100',
  },
  processando: {
    label: 'Processando',
    variant: 'secondary' as const,
    icon: Loader2,
    className: 'bg-blue-100 text-blue-800 hover:bg-blue-100',
  },
  processing: {
    label: 'Processando',
    variant: 'secondary' as const,
    icon: Loader2,
    className: 'bg-blue-100 text-blue-800 hover:bg-blue-100',
  },
  em_execucao: {
    label: 'Em Execução',
    variant: 'secondary' as const,
    icon: Loader2,
    className: 'bg-blue-100 text-blue-800 hover:bg-blue-100',
  },
  concluido: {
    label: 'Concluído',
    variant: 'secondary' as const,
    icon: CheckCircle2,
    className: 'bg-green-100 text-green-800 hover:bg-green-100',
  },
  completed: {
    label: 'Concluído',
    variant: 'secondary' as const,
    icon: CheckCircle2,
    className: 'bg-green-100 text-green-800 hover:bg-green-100',
  },
  erro: {
    label: 'Erro',
    variant: 'destructive' as const,
    icon: AlertCircle,
    className: 'bg-red-100 text-red-800 hover:bg-red-100',
  },
  failed: {
    label: 'Erro',
    variant: 'destructive' as const,
    icon: AlertCircle,
    className: 'bg-red-100 text-red-800 hover:bg-red-100',
  },
};

export function StatusTag({ status }: StatusTagProps) {
  const config = statusConfig[status] || statusConfig['pendente']; // Default to pendente if unknown
  const Icon = config.icon;

  return (
    <Badge variant={config.variant} className={`${config.className} flex items-center gap-1 w-fit`}>
      <Icon className={`h-3 w-3 ${status === 'processando' ? 'animate-spin' : ''}`} />
      {config.label}
    </Badge>
  );
}

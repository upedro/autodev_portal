import { Download, RefreshCw, Eye } from 'lucide-react';
import { Button } from './ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { StatusTag } from './StatusTag';
import { Solicitacao } from '../api';
import { Badge } from './ui/badge';
import { useNavigate } from 'react-router-dom';

interface TableSolicitacoesProps {
  solicitacoes: Solicitacao[];
  loading?: boolean;
  onRefresh?: () => void;
  onDownload?: (id: string) => void;
}

export function TableSolicitacoes({
  solicitacoes,
  loading = false,
  onRefresh,
  onDownload,
}: TableSolicitacoesProps) {
  const navigate = useNavigate();

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

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <p className="text-sm text-gray-600">
          Total: {solicitacoes.length} solicitações
        </p>
        {onRefresh && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
        )}
      </div>

      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Cliente</TableHead>
              <TableHead>Serviço</TableHead>
              <TableHead>CNJs</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Data</TableHead>
              <TableHead className="text-right">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {solicitacoes.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                  Nenhuma solicitação encontrada
                </TableCell>
              </TableRow>
            ) : (
              solicitacoes.map((solicitacao) => (
                <TableRow key={solicitacao.id}>
                  <TableCell>{solicitacao.cliente_nome}</TableCell>
                  <TableCell>{solicitacao.servico}</TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {solicitacao.cnjs.length} {solicitacao.cnjs.length === 1 ? 'processo' : 'processos'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <StatusTag status={solicitacao.status} />
                  </TableCell>
                  <TableCell className="text-sm text-gray-600">
                    {formatDate(solicitacao.created_at)}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/solicitacao/${solicitacao.id}`)}
                        title="Ver detalhes"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      {solicitacao.status === 'concluido' && onDownload && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onDownload(solicitacao.id)}
                          title="Baixar resultado"
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

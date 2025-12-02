import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { ServiceSelector } from '../components/ServiceSelector';
import { FileUploader } from '../components/FileUploader';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Cliente, clientesAPI, solicitacoesAPI } from '../api';
import { parseCNJList, validateCNJ } from '../utils/formatCnj';
import { ArrowLeft, ArrowRight, Send, Loader2 } from 'lucide-react';
import { toast } from 'sonner@2.0.3';
import { Badge } from '../components/ui/badge';

export function SolicitarServico() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Form state
  const [clienteId, setClienteId] = useState('');
  const [servico, setServico] = useState('buscar_documentos');
  const [cnjsText, setCnjsText] = useState('');
  const [cnjsFromFile, setCnjsFromFile] = useState<string[]>([]);
  const [inputMode, setInputMode] = useState<'manual' | 'file'>('manual');

  useEffect(() => {
    const loadClientes = async () => {
      try {
        const data = await clientesAPI.list();
        setClientes(data);
      } catch (error) {
        toast.error('Erro ao carregar clientes');
      }
    };
    loadClientes();
  }, []);

  const getCNJList = (): string[] => {
    if (inputMode === 'file') {
      return cnjsFromFile;
    }
    return parseCNJList(cnjsText);
  };

  const validateStep1 = () => {
    if (!clienteId) {
      toast.error('Selecione um cliente');
      return false;
    }
    if (!servico) {
      toast.error('Selecione um serviço');
      return false;
    }
    return true;
  };

  const validateStep2 = () => {
    const cnjs = getCNJList();
    if (cnjs.length === 0) {
      toast.error('Insira pelo menos um número CNJ');
      return false;
    }

    const invalidCNJs = cnjs.filter(cnj => !validateCNJ(cnj));
    if (invalidCNJs.length > 0) {
      toast.error(`${invalidCNJs.length} CNJ(s) com formato inválido`);
      return false;
    }

    return true;
  };

  const handleNext = () => {
    if (step === 1 && validateStep1()) {
      setStep(2);
    } else if (step === 2 && validateStep2()) {
      setStep(3);
    }
  };

  const handleSubmit = async () => {
    if (!validateStep1() || !validateStep2()) return;

    setLoading(true);
    try {
      const cnjs = getCNJList();
      await solicitacoesAPI.create({
        cliente_id: clienteId,
        servico,
        cnjs,
      });
      
      toast.success('Solicitação enviada com sucesso!');
      navigate('/acompanhamento');
    } catch (error) {
      toast.error('Erro ao enviar solicitação');
    } finally {
      setLoading(false);
    }
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="cliente">Cliente *</Label>
        <Select value={clienteId} onValueChange={setClienteId}>
          <SelectTrigger id="cliente">
            <SelectValue placeholder="Selecione o cliente" />
          </SelectTrigger>
          <SelectContent>
            {clientes.map((cliente) => (
              <SelectItem key={cliente.id} value={cliente.id}>
                {cliente.nome}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Serviço *</Label>
        <ServiceSelector value={servico} onChange={setServico} />
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label>Inserir Números CNJ *</Label>
        <Tabs value={inputMode} onValueChange={(v) => setInputMode(v as 'manual' | 'file')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="manual">Inserção Manual</TabsTrigger>
            <TabsTrigger value="file">Upload de Planilha</TabsTrigger>
          </TabsList>
          
          <TabsContent value="manual" className="space-y-2">
            <Textarea
              placeholder="Insira um número CNJ por linha&#10;0001234-56.2022.8.26.0100&#10;4000312-69.2025.8.26.0441"
              value={cnjsText}
              onChange={(e) => setCnjsText(e.target.value)}
              rows={8}
              className="font-mono text-sm"
            />
            <p className="text-xs text-gray-600">
              Insira um número CNJ por linha no formato: NNNNNNN-DD.AAAA.J.TR.OOOO
            </p>
          </TabsContent>
          
          <TabsContent value="file">
            <FileUploader onFileSelect={setCnjsFromFile} />
          </TabsContent>
        </Tabs>
      </div>

      {getCNJList().length > 0 && (
        <Alert>
          <AlertDescription>
            <strong>{getCNJList().length}</strong> número(s) CNJ {getCNJList().length === 1 ? 'detectado' : 'detectados'}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );

  const renderStep3 = () => {
    const cnjs = getCNJList();
    const cliente = clientes.find(c => c.id === clienteId);

    return (
      <div className="space-y-6">
        <Alert>
          <AlertDescription>
            Revise as informações antes de enviar a solicitação
          </AlertDescription>
        </Alert>

        <div className="space-y-4">
          <div>
            <Label className="text-gray-600">Cliente</Label>
            <p className="mt-1">{cliente?.nome}</p>
          </div>

          <div>
            <Label className="text-gray-600">Automação RPA</Label>
            <p className="mt-1">RPA - Buscar Documentos</p>
          </div>

          <div>
            <Label className="text-gray-600">Números CNJ</Label>
            <div className="mt-2 flex flex-wrap gap-2">
              {cnjs.slice(0, 5).map((cnj, idx) => (
                <Badge key={idx} variant="secondary">
                  {cnj}
                </Badge>
              ))}
              {cnjs.length > 5 && (
                <Badge variant="outline">
                  +{cnjs.length - 5} mais
                </Badge>
              )}
            </div>
            <p className="text-sm text-gray-600 mt-2">
              Total: {cnjs.length} {cnjs.length === 1 ? 'processo' : 'processos'}
            </p>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/dashboard')}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar
        </Button>
      </div>

      <div>
        <h1 className="text-3xl text-[#0d0d16]">Nova Demanda RPA</h1>
        <p className="text-gray-600 mt-1">
          Solicite uma automação de processos jurídicos via RPA
        </p>
      </div>

      {/* Progress indicator */}
      <div className="flex items-center justify-between">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center flex-1">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${
                s <= step
                  ? 'bg-[#3ecf8e] border-[#3ecf8e] text-[#0d0d16]'
                  : 'bg-white border-gray-300 text-gray-400'
              }`}
            >
              {s}
            </div>
            {s < 3 && (
              <div
                className={`flex-1 h-1 mx-2 ${
                  s < step ? 'bg-[#3ecf8e]' : 'bg-gray-200'
                }`}
              />
            )}
          </div>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            {step === 1 && 'Etapa 1: Cliente e Serviço'}
            {step === 2 && 'Etapa 2: Números CNJ'}
            {step === 3 && 'Etapa 3: Revisão'}
          </CardTitle>
          <CardDescription>
            {step === 1 && 'Selecione o escritório cliente e o tipo de automação RPA'}
            {step === 2 && 'Insira os números CNJ manualmente ou via upload de planilha'}
            {step === 3 && 'Revise e confirme os dados antes de enviar'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}
          {step === 3 && renderStep3()}

          <div className="flex justify-between mt-6 pt-6 border-t">
            <Button
              variant="outline"
              onClick={() => setStep(step - 1)}
              disabled={step === 1}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Anterior
            </Button>

            {step < 3 ? (
              <Button onClick={handleNext} className="bg-[#3ecf8e] hover:bg-[#35b87d] text-[#0d0d16]">
                Próximo
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            ) : (
              <Button onClick={handleSubmit} disabled={loading} className="bg-[#3ecf8e] hover:bg-[#35b87d] text-[#0d0d16]">
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Enviando...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Enviar Demanda
                  </>
                )}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

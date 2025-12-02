import { FileText, Search } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { RadioGroup, RadioGroupItem } from './ui/radio-group';
import { Label } from './ui/label';

interface Service {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
}

const services: Service[] = [
  {
    id: 'buscar_documentos',
    name: 'RPA - Buscar Documentos',
    description: 'Automação para busca e download de documentos processuais via tribunais',
    icon: <FileText className="h-5 w-5" />,
  },
  {
    id: 'consultar_andamento',
    name: 'RPA - Consultar Andamento',
    description: 'Automação de consulta de andamentos processuais (em breve)',
    icon: <Search className="h-5 w-5" />,
  },
];

interface ServiceSelectorProps {
  value: string;
  onChange: (value: string) => void;
}

export function ServiceSelector({ value, onChange }: ServiceSelectorProps) {
  return (
    <div className="space-y-4">
      <RadioGroup value={value} onValueChange={onChange}>
        {services.map((service) => (
          <Card
            key={service.id}
            className={`cursor-pointer transition-all ${
              value === service.id
                ? 'border-[#3ecf8e] bg-[#3ecf8e]/5'
                : 'hover:border-gray-400'
            } ${service.id !== 'buscar_documentos' ? 'opacity-50' : ''}`}
          >
            <CardHeader className="pb-3">
              <div className="flex items-start gap-4">
                <RadioGroupItem
                  value={service.id}
                  id={service.id}
                  disabled={service.id !== 'buscar_documentos'}
                  className="mt-1"
                />
                <div className="flex-1">
                  <Label
                    htmlFor={service.id}
                    className="cursor-pointer flex items-center gap-2"
                  >
                    {service.icon}
                    <CardTitle className="text-base">{service.name}</CardTitle>
                  </Label>
                  <CardDescription className="mt-1.5">
                    {service.description}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
          </Card>
        ))}
      </RadioGroup>
    </div>
  );
}

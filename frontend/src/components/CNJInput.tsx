import { useState } from 'react';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { formatCNJ, validateCNJ } from '../utils/formatCnj';
import { CheckCircle2, XCircle } from 'lucide-react';

interface CNJInputProps {
  value: string;
  onChange: (value: string) => void;
  label?: string;
  error?: string;
}

export function CNJInput({ value, onChange, label = 'Número CNJ', error }: CNJInputProps) {
  const [touched, setTouched] = useState(false);
  const isValid = validateCNJ(value);
  const showValidation = touched && value.length > 0;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatCNJ(e.target.value);
    onChange(formatted);
  };

  const handleBlur = () => {
    setTouched(true);
  };

  return (
    <div className="space-y-2">
      <Label htmlFor="cnj-input">{label}</Label>
      <div className="relative">
        <Input
          id="cnj-input"
          type="text"
          value={value}
          onChange={handleChange}
          onBlur={handleBlur}
          placeholder="0001234-56.2022.8.26.0100"
          maxLength={25}
          className={`pr-10 ${error ? 'border-red-500' : ''} ${showValidation && isValid ? 'border-green-500' : ''}`}
        />
        {showValidation && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            {isValid ? (
              <CheckCircle2 className="h-5 w-5 text-green-500" />
            ) : (
              <XCircle className="h-5 w-5 text-red-500" />
            )}
          </div>
        )}
      </div>
      {error && <p className="text-sm text-red-500">{error}</p>}
      {showValidation && !isValid && !error && (
        <p className="text-sm text-red-500">
          Formato inválido. Use: NNNNNNN-DD.AAAA.J.TR.OOOO
        </p>
      )}
    </div>
  );
}

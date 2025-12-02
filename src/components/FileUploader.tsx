import { useCallback, useState } from 'react';
import { Upload, FileSpreadsheet, X } from 'lucide-react';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';

interface FileUploaderProps {
  onFileSelect: (cnjs: string[]) => void;
  onFileChange?: (file: File | null) => void;
}

export function FileUploader({ onFileSelect, onFileChange }: FileUploaderProps) {
  const [fileName, setFileName] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [file, setFile] = useState<File | null>(null);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setError('');

    if (!selectedFile.name.endsWith('.xlsx') && !selectedFile.name.endsWith('.xls')) {
      setError('Por favor, selecione um arquivo .xlsx ou .xls');
      return;
    }

    setFileName(selectedFile.name);
    setFile(selectedFile);

    // Notify parent component about file change
    if (onFileChange) {
      onFileChange(selectedFile);
    }

    // Parse file using xlsx library (client-side preview)
    import('xlsx').then((XLSX) => {
      const reader = new FileReader();

      reader.onload = (e) => {
        try {
          const data = e.target?.result;
          const workbook = XLSX.read(data, { type: 'binary' });

          // Get first sheet
          const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
          const jsonData = XLSX.utils.sheet_to_json(firstSheet, { header: 1 });

          // Find CNJ column
          const headers = jsonData[0] as string[];
          const cnjColumnIndex = headers.findIndex((h: string) =>
            h && h.toString().toUpperCase().trim() === 'CNJ'
          );

          const cnjs: string[] = [];

          if (cnjColumnIndex !== -1) {
            // Parse from CNJ column
            for (let i = 1; i < jsonData.length; i++) {
              const row = jsonData[i] as any[];
              const cnj = row[cnjColumnIndex];
              if (cnj) {
                cnjs.push(cnj.toString().trim());
              }
            }
          }

          // Notify parent with extracted CNJs
          onFileSelect(cnjs);

        } catch (err) {
          setError('Erro ao ler arquivo. Verifique o formato.');
        }
      };

      reader.readAsBinaryString(selectedFile);
    }).catch(() => {
      // Fallback: just store file and let backend parse
      onFileSelect([]);
    });
  }, [onFileSelect, onFileChange]);

  const handleClear = () => {
    setFileName('');
    setError('');
    setFile(null);
    onFileSelect([]);
    if (onFileChange) {
      onFileChange(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="border-2 border-dashed rounded-lg p-8 text-center hover:border-gray-400 transition-colors">
        {!fileName ? (
          <label className="cursor-pointer">
            <input
              type="file"
              className="hidden"
              accept=".xlsx,.xls,.csv"
              onChange={handleFileChange}
            />
            <div className="flex flex-col items-center gap-3">
              <Upload className="h-12 w-12 text-gray-400" />
              <div>
                <p className="text-sm text-gray-600">
                  Arraste um arquivo ou <span className="text-blue-600">clique para selecionar</span>
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Formatos aceitos: .xlsx, .xls, .csv
                </p>
              </div>
            </div>
          </label>
        ) : (
          <div className="flex items-center justify-center gap-3">
            <FileSpreadsheet className="h-8 w-8 text-green-600" />
            <div className="flex-1 text-left">
              <p className="text-sm">{fileName}</p>
              <p className="text-xs text-gray-500">Arquivo carregado com sucesso</p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClear}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Alert>
        <AlertDescription className="text-xs">
          <strong>Formato esperado:</strong> A planilha deve conter uma coluna chamada "CNJ" com os números dos processos.
        </AlertDescription>
      </Alert>
    </div>
  );
}

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { useAuthStore } from '../store/useAuthStore';
import { authAPI } from '../api';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner@2.0.3';
import logoAutodev from 'figma:asset/b1e31574b91d7617bb70e19644af8b0ae6763242.png';

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authAPI.login({ email, senha: password });
      setAuth(response.user, response.access_token);
      toast.success('Login realizado com sucesso!');
      navigate('/dashboard');
    } catch (err) {
      setError('Credenciais inválidas. Tente novamente.');
      toast.error('Falha no login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0d0d16] p-4 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-[#3ecf8e]/10 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-[#3ecf8e]/10 rounded-full blur-3xl"></div>
      </div>

      <Card className="w-full max-w-md relative z-10 border-[#dee1e4]/20">
        <CardHeader className="space-y-6 text-center">
          <div className="mx-auto">
            <img src={logoAutodev} alt="Autodev" className="h-16 mx-auto" />
          </div>
          <div>
            <CardTitle className="text-2xl">Portal de Automação RPA</CardTitle>
            <CardDescription className="mt-2">
              Plataforma para escritórios de advocacia solicitarem automações e processos via RPA
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">E-mail do escritório</Label>
              <Input
                id="email"
                type="email"
                placeholder="contato@escritorio.com.br"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Senha</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Entrando...
                </>
              ) : (
                'Acessar plataforma'
              )}
            </Button>

            <div className="mt-4 p-3 bg-[#3ecf8e]/10 border border-[#3ecf8e]/20 rounded-lg">
              <p className="text-xs text-[#3ecf8e]">
                <strong>Demo:</strong> Use <code className="bg-[#0d0d16]/30 px-1.5 py-0.5 rounded">admin@portal-rpa.com</code> e senha <code className="bg-[#0d0d16]/30 px-1.5 py-0.5 rounded">admin123</code>
              </p>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

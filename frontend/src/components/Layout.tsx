import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { useAuthStore } from '../store/useAuthStore';
import { LogOut, LayoutDashboard, FileText, Eye } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { Avatar, AvatarFallback } from './ui/avatar';
import logoAutodev from 'figma:asset/b1e31574b91d7617bb70e19644af8b0ae6763242.png';

export function Layout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/solicitar', label: 'Nova Demanda', icon: FileText },
    { path: '/acompanhamento', label: 'Acompanhamento', icon: Eye },
  ];

  const getInitials = (name: string | undefined) => {
    if (!name) return 'U';
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div className="min-h-screen bg-[#f8f9fa]">
      <header className="bg-[#0d0d16] border-b border-[#dee1e4]/10 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-8">
              <button onClick={() => navigate('/dashboard')} className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                <img src={logoAutodev} alt="Autodev" className="h-8" />
                <div className="hidden sm:block">
                  <p className="text-xs text-[#dee1e4]">Portal RPA</p>
                </div>
              </button>

              <nav className="hidden md:flex items-center gap-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  return (
                    <Button
                      key={item.path}
                      variant={isActive ? 'secondary' : 'ghost'}
                      onClick={() => navigate(item.path)}
                      className={`gap-2 ${
                        isActive 
                          ? 'bg-[#3ecf8e] text-[#0d0d16] hover:bg-[#3ecf8e]/90' 
                          : 'text-[#dee1e4] hover:bg-[#dee1e4]/10'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      {item.label}
                    </Button>
                  );
                })}
              </nav>
            </div>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="gap-2 text-[#dee1e4] hover:bg-[#dee1e4]/10">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-[#3ecf8e] text-[#0d0d16]">
                      {user ? getInitials(user.nome) : 'U'}
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden md:inline">{user?.nome}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div>
                    <p>{user?.nome}</p>
                    <p className="text-xs text-gray-600">{user?.email}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                  <LogOut className="h-4 w-4 mr-2" />
                  Sair
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 pb-20">
        <Outlet />
      </main>

      <footer className="border-t bg-white py-6 mt-auto">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <img src={logoAutodev} alt="Autodev" className="h-6" />
              <span className="text-sm text-gray-600">
                © 2025 Autodev - Automação Inteligente para Escritórios de Advocacia
              </span>
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span>Portal RPA v1.0</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

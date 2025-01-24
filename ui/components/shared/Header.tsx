import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { UserCircle, Settings, LogOut } from 'lucide-react';

const Header: React.FC = () => {
  const router = useRouter();
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);

  return (
    <header className="w-full bg-white shadow">
      <div className="container mx-auto px-4 py-3 flex justify-between items-center">
        <Link href="/dashboard">
          <span className="text-xl font-bold text-gray-800">Clarity</span>
        </Link>

        <nav className="hidden md:flex space-x-6">
          <Link href="/dashboard" className={`text-gray-600 hover:text-gray-900 ${router.pathname === '/dashboard' ? 'text-gray-900' : ''}`}>
            Dashboard
          </Link>
          <Link href="/insights" className={`text-gray-600 hover:text-gray-900 ${router.pathname === '/insights' ? 'text-gray-900' : ''}`}>
            Insights
          </Link>
          <Link href="/settings" className={`text-gray-600 hover:text-gray-900 ${router.pathname === '/settings' ? 'text-gray-900' : ''}`}>
            Settings
          </Link>
        </nav>

        <div className="relative">
          <button
            className="flex items-center space-x-2 text-gray-600 hover:text-gray-900"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            <UserCircle className="w-6 h-6" />
            <span>John Doe</span>
          </button>

          {isMenuOpen && (
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1">
              <Link href="/profile" className="block px-4 py-2 text-gray-800 hover:bg-gray-100">
                Profile
              </Link>
              <Link href="/settings" className="block px-4 py-2 text-gray-800 hover:bg-gray-100">
                Settings
              </Link>
              <button className="w-full text-left px-4 py-2 text-gray-800 hover:bg-gray-100">
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;

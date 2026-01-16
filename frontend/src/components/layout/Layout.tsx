import React, { ReactNode } from "react";
import { useAuth } from "../../contexts/AuthContext";
import Navigation from "./Navigation";

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      {isAuthenticated && <Navigation />}
      <main className={isAuthenticated ? "pt-16" : ""}>{children}</main>
    </div>
  );
};

export default Layout;

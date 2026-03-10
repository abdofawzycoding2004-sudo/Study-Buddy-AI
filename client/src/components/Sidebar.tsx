import { Link, useLocation } from "wouter";
import { BookOpen, BrainCircuit, MessageSquare, Library } from "lucide-react";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const [location] = useLocation();

  const links = [
    { href: "/materials", label: "Study Materials", icon: Library },
    { href: "/quizzes", label: "Quizzes", icon: BrainCircuit },
    { href: "/chat", label: "Tutor Chat", icon: MessageSquare },
  ];

  return (
    <aside className="w-64 bg-card border-r border-border min-h-screen flex flex-col fixed left-0 top-0">
      <div className="p-6 border-b border-border flex items-center gap-3">
        <div className="bg-primary p-2 rounded-xl shadow-lg shadow-primary/20">
          <BookOpen className="w-6 h-6 text-primary-foreground" />
        </div>
        <h1 className="text-2xl font-bold font-display text-primary">AI Tutor</h1>
      </div>
      
      <nav className="p-4 flex-1 space-y-2">
        {links.map((link) => {
          const isActive = location.startsWith(link.href) || (location === "/" && link.href === "/materials");
          const Icon = link.icon;
          
          return (
            <Link key={link.href} href={link.href} 
              className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-all duration-200 group",
                isActive 
                  ? "bg-primary text-primary-foreground shadow-md shadow-primary/20" 
                  : "text-muted-foreground hover:bg-secondary hover:text-primary"
              )}
            >
              <Icon className={cn("w-5 h-5", isActive ? "text-primary-foreground" : "text-muted-foreground group-hover:text-primary")} />
              {link.label}
            </Link>
          );
        })}
      </nav>
      
      <div className="p-6 text-xs text-muted-foreground text-center border-t border-border">
        Powered by AI Integrations
      </div>
    </aside>
  );
}

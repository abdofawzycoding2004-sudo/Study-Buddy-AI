import { Switch, Route, Redirect } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/not-found";

import { Sidebar } from "@/components/Sidebar";
import MaterialsPage from "@/pages/MaterialsPage";
import MaterialViewPage from "@/pages/MaterialViewPage";
import QuizzesPage from "@/pages/QuizzesPage";
import QuizTakePage from "@/pages/QuizTakePage";
import ChatPage from "@/pages/ChatPage";

function Router() {
  return (
    <div className="flex min-h-screen">
      <div className="hidden md:block">
        <Sidebar />
      </div>
      <main className="flex-1 md:ml-64 w-full">
        <Switch>
          <Route path="/">
            <Redirect to="/materials" />
          </Route>
          <Route path="/materials" component={MaterialsPage} />
          <Route path="/materials/:id" component={MaterialViewPage} />
          <Route path="/quizzes" component={QuizzesPage} />
          <Route path="/quizzes/:id" component={QuizTakePage} />
          <Route path="/chat" component={ChatPage} />
          <Route path="/chat/:id" component={ChatPage} />
          <Route component={NotFound} />
        </Switch>
      </main>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Router />
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;

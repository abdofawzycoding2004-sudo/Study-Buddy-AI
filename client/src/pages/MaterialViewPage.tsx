import { useParams } from "wouter";
import { useMaterial } from "@/hooks/use-materials";
import { useGenerateQuiz } from "@/hooks/use-quizzes";
import { useCreateConversation } from "@/hooks/use-chat";
import { motion } from "framer-motion";
import { BrainCircuit, MessageSquare, ArrowLeft, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "wouter";
import { MarkdownView } from "@/components/MarkdownView";

export default function MaterialViewPage() {
  const params = useParams();
  const id = parseInt(params.id || "0");
  
  const { data: material, isLoading } = useMaterial(id);
  const generateQuizMutation = useGenerateQuiz();
  const createChatMutation = useCreateConversation();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="w-12 h-12 animate-spin text-primary/50" />
      </div>
    );
  }

  if (!material) {
    return (
      <div className="p-8 text-center">
        <h2 className="text-2xl font-bold font-display">Material not found</h2>
        <Link href="/materials" className="text-primary hover:underline mt-4 inline-block">Return to Materials</Link>
      </div>
    );
  }

  const handleAskTutor = () => {
    createChatMutation.mutate({ title: `Discussion: ${material.title}` });
  };

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="p-8 max-w-5xl mx-auto"
    >
      <Link href="/materials" className="inline-flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors mb-6 font-medium">
        <ArrowLeft className="w-4 h-4" /> Back to Materials
      </Link>

      <div className="bg-card rounded-3xl p-8 md:p-12 shadow-sm border border-border">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10 pb-8 border-b border-border">
          <h1 className="text-4xl md:text-5xl font-bold font-display text-foreground leading-tight">
            {material.title}
          </h1>
          
          <div className="flex flex-wrap gap-4 shrink-0">
            <Button 
              onClick={() => generateQuizMutation.mutate(material.id)}
              disabled={generateQuizMutation.isPending}
              variant="outline" 
              className="rounded-xl px-6 py-6 border-primary/20 text-primary hover:bg-primary/5 hover:text-primary text-base gap-2"
            >
              {generateQuizMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : <BrainCircuit className="w-5 h-5" />}
              {generateQuizMutation.isPending ? "Generating..." : "Generate Quiz"}
            </Button>
            
            <Button 
              onClick={handleAskTutor}
              disabled={createChatMutation.isPending}
              className="rounded-xl px-6 py-6 shadow-lg shadow-primary/20 hover:shadow-xl hover:-translate-y-0.5 transition-all text-base gap-2"
            >
              {createChatMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : <MessageSquare className="w-5 h-5" />}
              Ask AI Tutor
            </Button>
          </div>
        </div>

        <div className="bg-secondary/30 rounded-2xl p-6 md:p-10 border border-border/50">
          <MarkdownView content={material.content} />
        </div>
      </div>
    </motion.div>
  );
}

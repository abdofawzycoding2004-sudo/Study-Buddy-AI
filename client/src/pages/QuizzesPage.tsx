import { useQuizzes } from "@/hooks/use-quizzes";
import { Link } from "wouter";
import { motion } from "framer-motion";
import { BrainCircuit, Play, Loader2 } from "lucide-react";
import { format } from "date-fns";

export default function QuizzesPage() {
  const { data: quizzes, isLoading } = useQuizzes();

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-8 max-w-7xl mx-auto"
    >
      <div className="mb-10">
        <h1 className="text-4xl font-bold font-display text-foreground mb-2">Practice Quizzes</h1>
        <p className="text-muted-foreground text-lg">Test your knowledge on the materials you've studied.</p>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center py-20">
          <Loader2 className="w-10 h-10 animate-spin text-primary/50" />
        </div>
      ) : quizzes?.length === 0 ? (
        <div className="text-center py-24 bg-card rounded-3xl border border-dashed border-border shadow-sm">
          <div className="bg-accent/10 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
            <BrainCircuit className="w-10 h-10 text-accent" />
          </div>
          <h3 className="text-2xl font-bold font-display mb-3">No quizzes generated</h3>
          <p className="text-muted-foreground max-w-sm mx-auto mb-6">Go to a study material and click "Generate Quiz" to create practice questions.</p>
          <Link href="/materials" className="inline-flex items-center justify-center rounded-xl bg-primary px-6 py-3 font-medium text-primary-foreground shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all hover:-translate-y-0.5">
            View Materials
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {quizzes?.map((quiz, i) => (
            <motion.div 
              key={quiz.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="bg-card rounded-2xl p-6 border border-border shadow-sm hover:shadow-xl hover:border-accent/40 transition-all duration-300 group flex flex-col"
            >
              <div className="bg-accent/10 w-12 h-12 rounded-xl flex items-center justify-center mb-6 text-accent">
                <BrainCircuit className="w-6 h-6" />
              </div>
              
              <h3 className="text-xl font-bold font-display mb-2">{quiz.title}</h3>
              <p className="text-muted-foreground text-sm mb-6 flex-1">
                Generated on {format(new Date(quiz.createdAt), "MMM d, yyyy")}
              </p>
              
              <Link href={`/quizzes/${quiz.id}`} className="flex items-center justify-center gap-2 w-full bg-secondary text-foreground hover:bg-accent hover:text-accent-foreground font-medium py-3 rounded-xl transition-colors">
                <Play className="w-4 h-4" /> Start Quiz
              </Link>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
}

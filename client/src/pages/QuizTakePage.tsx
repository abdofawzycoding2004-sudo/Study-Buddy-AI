import { useState } from "react";
import { useParams, Link } from "wouter";
import { useQuiz } from "@/hooks/use-quizzes";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, ArrowLeft, CheckCircle2, XCircle, ChevronRight, Award } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function QuizTakePage() {
  const params = useParams();
  const id = parseInt(params.id || "0");
  const { data: quiz, isLoading } = useQuiz(id);

  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [score, setScore] = useState(0);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="w-12 h-12 animate-spin text-primary/50" />
      </div>
    );
  }

  if (!quiz || !quiz.questions || quiz.questions.length === 0) {
    return (
      <div className="p-8 text-center">
        <h2 className="text-2xl font-bold font-display">Quiz not found or has no questions</h2>
        <Link href="/quizzes" className="text-primary hover:underline mt-4 inline-block">Return to Quizzes</Link>
      </div>
    );
  }

  const question = quiz.questions[currentIndex];
  const isFinished = currentIndex >= quiz.questions.length;

  const handleSubmit = () => {
    if (!selectedOption) return;
    setIsSubmitted(true);
    if (selectedOption === question.correctAnswer) {
      setScore(s => s + 1);
    }
  };

  const handleNext = () => {
    setSelectedOption(null);
    setIsSubmitted(false);
    setCurrentIndex(i => i + 1);
  };

  if (isFinished) {
    const percentage = Math.round((score / quiz.questions.length) * 100);
    return (
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="max-w-2xl mx-auto pt-20 p-8">
        <div className="bg-card rounded-3xl p-12 border border-border shadow-xl text-center">
          <div className="mx-auto w-24 h-24 bg-accent/20 rounded-full flex items-center justify-center mb-6">
            <Award className="w-12 h-12 text-accent" />
          </div>
          <h1 className="text-4xl font-bold font-display mb-4">Quiz Completed!</h1>
          <p className="text-2xl mb-8">You scored <span className="font-bold text-primary">{score}</span> out of {quiz.questions.length} ({percentage}%)</p>
          
          <div className="flex gap-4 justify-center">
            <Link href="/quizzes" className="inline-flex items-center justify-center rounded-xl bg-secondary px-6 py-3 font-medium hover:bg-secondary/80 transition-colors">
              Back to Quizzes
            </Link>
            <Button onClick={() => { setCurrentIndex(0); setScore(0); setIsSubmitted(false); setSelectedOption(null); }} className="rounded-xl px-6 py-3">
              Retake Quiz
            </Button>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto pt-10 p-8">
      <Link href="/quizzes" className="inline-flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors mb-8 font-medium">
        <ArrowLeft className="w-4 h-4" /> Exit Quiz
      </Link>

      <div className="mb-8 flex items-center justify-between">
        <h2 className="text-xl font-bold text-primary">{quiz.title}</h2>
        <div className="text-sm font-medium bg-secondary px-4 py-1.5 rounded-full">
          Question {currentIndex + 1} of {quiz.questions.length}
        </div>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={currentIndex}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          className="bg-card rounded-3xl p-8 md:p-10 border border-border shadow-lg"
        >
          <h3 className="text-2xl font-bold font-display mb-8 leading-relaxed">
            {question.questionText}
          </h3>

          <div className="space-y-4 mb-8">
            {question.options.map((option, idx) => {
              const isSelected = selectedOption === option;
              const isCorrect = isSubmitted && option === question.correctAnswer;
              const isWrongSelection = isSubmitted && isSelected && !isCorrect;

              let btnClass = "border-border hover:border-primary/50 hover:bg-secondary/50";
              if (isSelected && !isSubmitted) btnClass = "border-primary bg-primary/5 ring-2 ring-primary/20";
              if (isCorrect) btnClass = "border-green-500 bg-green-50 text-green-900";
              if (isWrongSelection) btnClass = "border-red-500 bg-red-50 text-red-900";

              return (
                <button
                  key={idx}
                  disabled={isSubmitted}
                  onClick={() => setSelectedOption(option)}
                  className={`w-full text-left p-6 rounded-2xl border-2 transition-all duration-200 flex justify-between items-center ${btnClass}`}
                >
                  <span className="text-lg">{option}</span>
                  {isCorrect && <CheckCircle2 className="w-6 h-6 text-green-500 shrink-0" />}
                  {isWrongSelection && <XCircle className="w-6 h-6 text-red-500 shrink-0" />}
                </button>
              );
            })}
          </div>

          {isSubmitted && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }} 
              animate={{ opacity: 1, height: "auto" }} 
              className="bg-secondary/50 rounded-2xl p-6 mb-8 border border-border"
            >
              <h4 className="font-bold mb-2 flex items-center gap-2">
                {selectedOption === question.correctAnswer ? (
                  <span className="text-green-600 flex items-center gap-2"><CheckCircle2 className="w-5 h-5"/> Correct!</span>
                ) : (
                  <span className="text-red-600 flex items-center gap-2"><XCircle className="w-5 h-5"/> Incorrect</span>
                )}
              </h4>
              <p className="text-muted-foreground leading-relaxed">{question.explanation}</p>
            </motion.div>
          )}

          <div className="flex justify-end border-t border-border pt-6">
            {!isSubmitted ? (
              <Button 
                onClick={handleSubmit} 
                disabled={!selectedOption}
                className="rounded-xl px-8 py-6 text-lg shadow-lg shadow-primary/20"
              >
                Check Answer
              </Button>
            ) : (
              <Button 
                onClick={handleNext} 
                className="rounded-xl px-8 py-6 text-lg bg-accent text-accent-foreground hover:bg-accent/90 shadow-lg shadow-accent/20"
              >
                {currentIndex === quiz.questions.length - 1 ? "Finish Quiz" : "Next Question"} <ChevronRight className="w-5 h-5 ml-2" />
              </Button>
            )}
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

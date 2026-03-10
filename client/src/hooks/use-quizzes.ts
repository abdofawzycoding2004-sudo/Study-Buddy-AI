import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, buildUrl } from "@shared/routes";
import { useToast } from "@/hooks/use-toast";
import { useLocation } from "wouter";

export function useQuizzes() {
  return useQuery({
    queryKey: [api.quizzes.list.path],
    queryFn: async () => {
      const res = await fetch(api.quizzes.list.path, { credentials: "include" });
      if (!res.ok) throw new Error("Failed to fetch quizzes");
      return api.quizzes.list.responses[200].parse(await res.json());
    },
  });
}

export function useQuiz(id: number) {
  return useQuery({
    queryKey: [api.quizzes.get.path, id],
    queryFn: async () => {
      const url = buildUrl(api.quizzes.get.path, { id });
      const res = await fetch(url, { credentials: "include" });
      if (res.status === 404) return null;
      if (!res.ok) throw new Error("Failed to fetch quiz");
      return api.quizzes.get.responses[200].parse(await res.json());
    },
    enabled: !!id,
  });
}

export function useGenerateQuiz() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [, setLocation] = useLocation();

  return useMutation({
    mutationFn: async (materialId: number) => {
      const res = await fetch(api.quizzes.generate.path, {
        method: api.quizzes.generate.method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ materialId }),
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to generate quiz");
      return api.quizzes.generate.responses[201].parse(await res.json());
    },
    onSuccess: (quiz) => {
      queryClient.invalidateQueries({ queryKey: [api.quizzes.list.path] });
      toast({ title: "Quiz generated successfully!" });
      setLocation(`/quizzes/${quiz.id}`);
    },
    onError: () => {
      toast({ title: "Failed to generate quiz", variant: "destructive" });
    }
  });
}

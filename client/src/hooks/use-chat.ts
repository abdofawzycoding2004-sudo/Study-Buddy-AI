import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, buildUrl } from "@shared/routes";
import { useState } from "react";
import { useToast } from "@/hooks/use-toast";
import { useLocation } from "wouter";

export function useConversations() {
  return useQuery({
    queryKey: [api.chat.conversations.list.path],
    queryFn: async () => {
      const res = await fetch(api.chat.conversations.list.path, { credentials: "include" });
      if (!res.ok) throw new Error("Failed to fetch conversations");
      return api.chat.conversations.list.responses[200].parse(await res.json());
    },
  });
}

export function useConversation(id?: number) {
  return useQuery({
    queryKey: [api.chat.conversations.get.path, id],
    queryFn: async () => {
      if (!id) return null;
      const url = buildUrl(api.chat.conversations.get.path, { id });
      const res = await fetch(url, { credentials: "include" });
      if (res.status === 404) return null;
      if (!res.ok) throw new Error("Failed to fetch conversation");
      return api.chat.conversations.get.responses[200].parse(await res.json());
    },
    enabled: !!id,
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [, setLocation] = useLocation();

  return useMutation({
    mutationFn: async (data: { title?: string }) => {
      const res = await fetch(api.chat.conversations.create.path, {
        method: api.chat.conversations.create.method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to create conversation");
      return api.chat.conversations.create.responses[201].parse(await res.json());
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [api.chat.conversations.list.path] });
      setLocation(`/chat/${data.id}`);
    },
    onError: () => {
      toast({ title: "Failed to start conversation", variant: "destructive" });
    }
  });
}

export function useChatStream(conversationId?: number) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedResponse, setStreamedResponse] = useState("");
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const sendMessage = async (content: string) => {
    if (!conversationId) return;
    setIsStreaming(true);
    setStreamedResponse("");

    try {
      const res = await fetch(`/api/conversations/${conversationId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });

      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let completeText = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.content) {
                completeText += data.content;
                setStreamedResponse(completeText);
              }
              if (data.done) {
                break;
              }
              if (data.error) {
                throw new Error(data.error);
              }
            } catch (e) {
              console.error("Parse error chunk:", line, e);
            }
          }
        }
      }

      queryClient.invalidateQueries({ queryKey: [api.chat.conversations.get.path, conversationId] });
    } catch (error) {
      toast({ title: "Error communicating with AI", variant: "destructive" });
      console.error(error);
    } finally {
      setIsStreaming(false);
      setStreamedResponse("");
    }
  };

  return { sendMessage, isStreaming, streamedResponse };
}

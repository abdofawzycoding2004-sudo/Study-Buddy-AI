import { useState, useRef, useEffect } from "react";
import { useParams, Link } from "wouter";
import { useConversations, useConversation, useCreateConversation, useChatStream } from "@/hooks/use-chat";
import { MarkdownView } from "@/components/MarkdownView";
import { motion } from "framer-motion";
import { MessageSquare, Plus, Send, Loader2, Bot, User } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function ChatPage() {
  const params = useParams();
  const conversationId = params.id ? parseInt(params.id) : undefined;
  
  const { data: conversations } = useConversations();
  const { data: currentConversation, isLoading } = useConversation(conversationId);
  const createMutation = useCreateConversation();
  const { sendMessage, isStreaming, streamedResponse } = useChatStream(conversationId);

  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentConversation?.messages, streamedResponse]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    sendMessage(input);
    setInput("");
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar for Conversations */}
      <div className="w-80 border-r border-border bg-card flex flex-col hidden md:flex">
        <div className="p-4 border-b border-border">
          <Button 
            onClick={() => createMutation.mutate({ title: "New Chat" })}
            disabled={createMutation.isPending}
            className="w-full justify-start gap-2 rounded-xl py-6 bg-secondary text-foreground hover:bg-primary hover:text-primary-foreground transition-all"
          >
            <Plus className="w-5 h-5" /> New Chat
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {conversations?.map(conv => (
            <Link 
              key={conv.id} 
              href={`/chat/${conv.id}`}
              className={cn(
                "flex items-center gap-3 p-3 rounded-xl transition-all truncate text-sm font-medium",
                conv.id === conversationId 
                  ? "bg-primary/10 text-primary" 
                  : "hover:bg-secondary text-muted-foreground"
              )}
            >
              <MessageSquare className="w-4 h-4 shrink-0" />
              <span className="truncate">{conv.title}</span>
            </Link>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative h-full">
        {!conversationId ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
            <div className="w-24 h-24 bg-primary/5 rounded-full flex items-center justify-center mb-6">
              <Bot className="w-12 h-12 text-primary" />
            </div>
            <h2 className="text-3xl font-bold font-display mb-4">AI Tutor Assistant</h2>
            <p className="text-muted-foreground text-lg max-w-md mx-auto mb-8">
              Ask questions about your study materials, request explanations, or get step-by-step guidance.
            </p>
            <Button 
              onClick={() => createMutation.mutate({ title: "New Chat" })}
              className="rounded-xl px-8 py-6 text-lg shadow-lg shadow-primary/20 hover:-translate-y-0.5 transition-all"
            >
              Start a Conversation
            </Button>
          </div>
        ) : (
          <>
            {/* Header mobile */}
            <div className="md:hidden p-4 border-b border-border flex items-center gap-4 bg-card">
              <Link href="/chat" className="text-muted-foreground"><MessageSquare className="w-5 h-5"/></Link>
              <h2 className="font-bold truncate">{currentConversation?.title}</h2>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 md:p-8">
              <div className="max-w-3xl mx-auto space-y-6">
                {currentConversation?.messages.map((msg, i) => (
                  <motion.div 
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={cn(
                      "flex gap-4 max-w-[85%]",
                      msg.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
                    )}
                  >
                    <div className={cn(
                      "w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-sm",
                      msg.role === "user" ? "bg-accent text-accent-foreground" : "bg-primary text-primary-foreground"
                    )}>
                      {msg.role === "user" ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                    </div>
                    <div className={cn(
                      "p-5 rounded-2xl shadow-sm text-[15px] leading-relaxed",
                      msg.role === "user" 
                        ? "bg-card border border-border" 
                        : "bg-primary/5 border border-primary/10"
                    )}>
                      {msg.role === "user" ? (
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      ) : (
                        <MarkdownView content={msg.content} />
                      )}
                    </div>
                  </motion.div>
                ))}

                {isStreaming && streamedResponse && (
                  <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex gap-4 max-w-[85%] mr-auto"
                  >
                    <div className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center shrink-0 shadow-sm">
                      <Bot className="w-5 h-5" />
                    </div>
                    <div className="p-5 rounded-2xl shadow-sm text-[15px] leading-relaxed bg-primary/5 border border-primary/10">
                      <MarkdownView content={streamedResponse} />
                      <span className="inline-block w-2 h-4 bg-primary animate-pulse ml-1 align-middle" />
                    </div>
                  </motion.div>
                )}

                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Input */}
            <div className="p-4 md:p-8 bg-gradient-to-t from-background via-background to-transparent pb-8">
              <div className="max-w-3xl mx-auto">
                <form 
                  onSubmit={handleSend}
                  className="bg-card rounded-2xl border border-border shadow-lg p-2 pl-4 flex items-center focus-within:ring-2 ring-primary/20 transition-all"
                >
                  <Input 
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask the tutor anything..."
                    className="border-0 focus-visible:ring-0 px-0 h-12 text-base shadow-none bg-transparent"
                    disabled={isStreaming}
                  />
                  <Button 
                    type="submit" 
                    disabled={!input.trim() || isStreaming}
                    className="rounded-xl h-12 w-12 p-0 shrink-0 bg-primary hover:bg-primary/90 text-primary-foreground shadow-md"
                  >
                    {isStreaming ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                  </Button>
                </form>
                <div className="text-center mt-3 text-xs text-muted-foreground">
                  AI Tutor can make mistakes. Consider verifying important information.
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

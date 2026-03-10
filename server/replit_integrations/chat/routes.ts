import type { Express, Request, Response } from "express";
import OpenAI from "openai";
import { chatStorage } from "./storage";

// This is using Replit's AI Integrations service, which provides OpenRouter-compatible API access without requiring your own OpenRouter API key.
const openrouter = new OpenAI({
  baseURL: process.env.AI_INTEGRATIONS_OPENROUTER_BASE_URL,
  apiKey: process.env.AI_INTEGRATIONS_OPENROUTER_API_KEY,
});

export function registerChatRoutes(app: Express): void {
  // Get all conversations
  app.get("/api/conversations", async (req: Request, res: Response) => {
    try {
      const conversations = await chatStorage.getAllConversations();
      res.json(conversations);
    } catch (error) {
      console.error("Error fetching conversations:", error);
      res.status(500).json({ error: "Failed to fetch conversations" });
    }
  });

  // Get single conversation with messages
  app.get("/api/conversations/:id", async (req: Request, res: Response) => {
    try {
      const id = parseInt(req.params.id);
      const conversation = await chatStorage.getConversation(id);
      if (!conversation) {
        return res.status(404).json({ error: "Conversation not found" });
      }
      const messages = await chatStorage.getMessagesByConversation(id);
      res.json({ ...conversation, messages });
    } catch (error) {
      console.error("Error fetching conversation:", error);
      res.status(500).json({ error: "Failed to fetch conversation" });
    }
  });

  // Create new conversation
  app.post("/api/conversations", async (req: Request, res: Response) => {
    try {
      const { title } = req.body;
      const conversation = await chatStorage.createConversation(title || "New Chat");
      res.status(201).json(conversation);
    } catch (error) {
      console.error("Error creating conversation:", error);
      res.status(500).json({ error: "Failed to create conversation" });
    }
  });

  // Delete conversation
  app.delete("/api/conversations/:id", async (req: Request, res: Response) => {
    try {
      const id = parseInt(req.params.id);
      await chatStorage.deleteConversation(id);
      res.status(204).send();
    } catch (error) {
      console.error("Error deleting conversation:", error);
      res.status(500).json({ error: "Failed to delete conversation" });
    }
  });

  // Send message and get AI response (streaming)
  // Note: The model should be configured based on your requirements. 
  // Use the OpenRouter API to find available models.
  app.post("/api/conversations/:id/messages", async (req: Request, res: Response) => {
    try {
      const conversationId = parseInt(req.params.id);
      const { content, model = "meta-llama/llama-3.3-70b-instruct" } = req.body;

      // Save user message
      await chatStorage.createMessage(conversationId, "user", content);

      // Get conversation history for context
      const messages = await chatStorage.getMessagesByConversation(conversationId);
      const chatMessages = messages.map((m) => ({
        role: m.role as "user" | "assistant",
        content: m.content,
      }));

      // Set up SSE
      res.setHeader("Content-Type", "text/event-stream");
      res.setHeader("Cache-Control", "no-cache");
      res.setHeader("Connection", "keep-alive");

      const systemPrompt = `You are an expert AI tutor designed to help students deeply understand academic concepts. Your role is to act as a professional educator, not a general chatbot.

Your teaching philosophy:
- Prioritize understanding over memorization
- Break complex topics into clear, manageable steps
- Provide multiple diverse examples to reinforce learning
- Explicitly highlight common misconceptions and tricky points
- Ask follow-up questions to assess understanding
- Encourage critical thinking and curiosity

Your response structure:
1. **Clear Explanation**: Start with a simple, clear definition or overview
2. **Step-by-Step Breakdown**: Break the concept into logical steps (use numbered lists)
3. **Examples**: Provide 2-3 relevant examples with varying difficulty levels
4. **Common Mistakes**: Explicitly state what students often get wrong
5. **Key Takeaways**: Summarize the core concepts
6. **Follow-up Questions**: End with 1-2 questions to check understanding or extend learning

Math Formatting:
- Use LaTeX for all mathematical expressions
- Inline math: $(expression)$
- Block equations: $$(expression)$$
- Example: $f(x) = x^2 + 2x + 1$ or $$\\int_0^1 x^2 dx$$

Tone: Professional, patient, encouraging, and Socratic. Always maintain a teacher's perspective of wanting to genuinely help the student learn.`;

      // Stream response from OpenRouter
      const stream = await openrouter.chat.completions.create({
        model,
        messages: [
          {
            role: "system",
            content: systemPrompt
          },
          ...chatMessages
        ],
        stream: true,
        max_tokens: 8192,
      });

      let fullResponse = "";

      for await (const chunk of stream) {
        const content = chunk.choices[0]?.delta?.content || "";
        if (content) {
          fullResponse += content;
          res.write(`data: ${JSON.stringify({ content })}\n\n`);
        }
      }

      // Save assistant message
      await chatStorage.createMessage(conversationId, "assistant", fullResponse);

      res.write(`data: ${JSON.stringify({ done: true })}\n\n`);
      res.end();
    } catch (error) {
      console.error("Error sending message:", error);
      // Check if headers already sent (SSE streaming started)
      if (res.headersSent) {
        res.write(`data: ${JSON.stringify({ error: "Failed to send message" })}\n\n`);
        res.end();
      } else {
        res.status(500).json({ error: "Failed to send message" });
      }
    }
  });
}


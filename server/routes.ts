import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { api } from "@shared/routes";
import { z } from "zod";
import OpenAI from "openai";
import { registerChatRoutes } from "./replit_integrations/chat";

// Using Replit AI Integrations for OpenRouter
const openrouter = new OpenAI({
  baseURL: process.env.AI_INTEGRATIONS_OPENROUTER_BASE_URL,
  apiKey: process.env.AI_INTEGRATIONS_OPENROUTER_API_KEY,
});

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  // Register AI chat routes from the integration
  registerChatRoutes(app);

  app.get(api.materials.list.path, async (req, res) => {
    const materials = await storage.getMaterials();
    res.json(materials);
  });

  app.get(api.materials.get.path, async (req, res) => {
    const material = await storage.getMaterial(Number(req.params.id));
    if (!material) {
      return res.status(404).json({ message: "Material not found" });
    }
    res.json(material);
  });

  app.post(api.materials.create.path, async (req, res) => {
    try {
      const input = api.materials.create.input.parse(req.body);
      const material = await storage.createMaterial(input);
      res.status(201).json(material);
    } catch (err) {
      if (err instanceof z.ZodError) {
        return res.status(400).json({
          message: err.errors[0].message,
          field: err.errors[0].path.join("."),
        });
      }
      throw err;
    }
  });

  app.delete(api.materials.delete.path, async (req, res) => {
    try {
      await storage.deleteMaterial(Number(req.params.id));
      res.status(204).send();
    } catch (err) {
      res.status(500).json({ message: "Failed to delete material" });
    }
  });

  app.get(api.quizzes.list.path, async (req, res) => {
    const quizzes = await storage.getQuizzes();
    res.json(quizzes);
  });

  app.get(api.quizzes.get.path, async (req, res) => {
    const quiz = await storage.getQuiz(Number(req.params.id));
    if (!quiz) {
      return res.status(404).json({ message: "Quiz not found" });
    }
    res.json(quiz);
  });

  app.post(api.quizzes.generate.path, async (req, res) => {
    try {
      const { materialId } = api.quizzes.generate.input.parse(req.body);
      const material = await storage.getMaterial(materialId);
      
      if (!material) {
        return res.status(404).json({ message: "Material not found" });
      }

      // Generate quiz using OpenRouter with teacher system prompt
      const quizSystemPrompt = `You are an expert AI tutor creating an educational quiz. Create a multiple choice quiz that tests deeper understanding, not just recall.

Requirements:
- Each question should test conceptual understanding
- Include one correct answer and three plausible distractors
- Provide clear explanations for why the correct answer is right
- Use LaTeX for mathematical expressions: $(expression)$ for inline, $$(expression)$$ for block equations
- Format: { "title": "Quiz Title", "questions": [{ "questionText": "...", "options": ["A", "B", "C", "D"], "correctAnswer": "...", "explanation": "Clear explanation with LaTeX if needed" }] }`;
      
      const response = await openrouter.chat.completions.create({
        model: "meta-llama/llama-3.3-70b-instruct",
        messages: [
          {
            role: "system",
            content: quizSystemPrompt
          },
          {
            role: "user",
            content: `Material:\n${material.content.substring(0, 4000)}`
          }
        ],
        response_format: { type: "json_object" },
      });

      const resultText = response.choices[0]?.message?.content || "{}";
      const generatedQuiz = JSON.parse(resultText);

      if (!generatedQuiz.questions || !Array.isArray(generatedQuiz.questions)) {
        throw new Error("Failed to generate valid quiz questions");
      }

      // Save to database
      const quiz = await storage.createQuiz(
        { title: generatedQuiz.title || `Quiz for ${material.title}`, materialId },
        generatedQuiz.questions
      );

      res.status(201).json(quiz);
    } catch (err) {
      console.error("Quiz generation error:", err);
      if (err instanceof z.ZodError) {
        return res.status(400).json({
          message: err.errors[0].message,
          field: err.errors[0].path.join("."),
        });
      }
      res.status(500).json({ message: "Failed to generate quiz" });
    }
  });

  return httpServer;
}

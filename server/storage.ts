import { materials, quizzes, questions, type InsertMaterial, type Material, type InsertQuiz, type Quiz, type InsertQuestion, type Question, type QuizWithQuestions } from "@shared/schema";
import { db } from "./db";
import { eq } from "drizzle-orm";

export interface IStorage {
  // Materials
  getMaterials(): Promise<Material[]>;
  getMaterial(id: number): Promise<Material | undefined>;
  createMaterial(material: InsertMaterial): Promise<Material>;
  deleteMaterial(id: number): Promise<void>;

  // Quizzes
  getQuizzes(): Promise<Quiz[]>;
  getQuiz(id: number): Promise<QuizWithQuestions | undefined>;
  createQuiz(quiz: InsertQuiz, quizQuestions: InsertQuestion[]): Promise<QuizWithQuestions>;
  
  // Also expose chat storage
}

export class DatabaseStorage implements IStorage {
  async getMaterials(): Promise<Material[]> {
    return await db.select().from(materials);
  }

  async getMaterial(id: number): Promise<Material | undefined> {
    const [material] = await db.select().from(materials).where(eq(materials.id, id));
    return material;
  }

  async createMaterial(insertMaterial: InsertMaterial): Promise<Material> {
    const [material] = await db.insert(materials).values(insertMaterial).returning();
    return material;
  }

  async deleteMaterial(id: number): Promise<void> {
    await db.delete(materials).where(eq(materials.id, id));
  }

  async getQuizzes(): Promise<Quiz[]> {
    return await db.select().from(quizzes);
  }

  async getQuiz(id: number): Promise<QuizWithQuestions | undefined> {
    const [quiz] = await db.select().from(quizzes).where(eq(quizzes.id, id));
    if (!quiz) return undefined;

    const quizQuestions = await db.select().from(questions).where(eq(questions.quizId, id));
    return { ...quiz, questions: quizQuestions };
  }

  async createQuiz(insertQuiz: InsertQuiz, quizQuestions: Omit<InsertQuestion, "quizId">[]): Promise<QuizWithQuestions> {
    const [quiz] = await db.insert(quizzes).values(insertQuiz).returning();
    
    const questionsToInsert = quizQuestions.map(q => ({
      ...q,
      quizId: quiz.id
    }));
    
    const insertedQuestions = await db.insert(questions).values(questionsToInsert).returning();
    
    return { ...quiz, questions: insertedQuestions };
  }
}

export const storage = new DatabaseStorage();

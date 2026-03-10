import { z } from "zod";
import { insertMaterialSchema, materials, quizzes, questions, conversations, messages } from "./schema";

export const errorSchemas = {
  validation: z.object({
    message: z.string(),
    field: z.string().optional(),
  }),
  notFound: z.object({
    message: z.string(),
  }),
  internal: z.object({
    message: z.string(),
  }),
};

export const api = {
  materials: {
    list: {
      method: "GET" as const,
      path: "/api/materials" as const,
      responses: {
        200: z.array(z.custom<typeof materials.$inferSelect>()),
      },
    },
    get: {
      method: "GET" as const,
      path: "/api/materials/:id" as const,
      responses: {
        200: z.custom<typeof materials.$inferSelect>(),
        404: errorSchemas.notFound,
      },
    },
    create: {
      method: "POST" as const,
      path: "/api/materials" as const,
      input: insertMaterialSchema,
      responses: {
        201: z.custom<typeof materials.$inferSelect>(),
        400: errorSchemas.validation,
      },
    },
    delete: {
      method: "DELETE" as const,
      path: "/api/materials/:id" as const,
      responses: {
        204: z.void(),
        404: errorSchemas.notFound,
      },
    }
  },
  quizzes: {
    list: {
      method: "GET" as const,
      path: "/api/quizzes" as const,
      responses: {
        200: z.array(z.custom<typeof quizzes.$inferSelect>()),
      },
    },
    get: {
      method: "GET" as const,
      path: "/api/quizzes/:id" as const,
      responses: {
        200: z.custom<typeof quizzes.$inferSelect & { questions: typeof questions.$inferSelect[] }>(),
        404: errorSchemas.notFound,
      },
    },
    generate: {
      method: "POST" as const,
      path: "/api/quizzes/generate" as const,
      input: z.object({ materialId: z.number() }),
      responses: {
        201: z.custom<typeof quizzes.$inferSelect>(),
        400: errorSchemas.validation,
      }
    }
  },
  // Chat APIs are handled by integration routes, but we define types here for frontend
  chat: {
    conversations: {
      list: {
        method: "GET" as const,
        path: "/api/conversations" as const,
        responses: {
          200: z.array(z.custom<typeof conversations.$inferSelect>()),
        },
      },
      get: {
        method: "GET" as const,
        path: "/api/conversations/:id" as const,
        responses: {
          200: z.custom<typeof conversations.$inferSelect & { messages: typeof messages.$inferSelect[] }>(),
        }
      },
      create: {
        method: "POST" as const,
        path: "/api/conversations" as const,
        input: z.object({ title: z.string().optional() }),
        responses: {
          201: z.custom<typeof conversations.$inferSelect>(),
        }
      },
      delete: {
        method: "DELETE" as const,
        path: "/api/conversations/:id" as const,
        responses: {
          204: z.void(),
        }
      }
    }
  }
};

export function buildUrl(path: string, params?: Record<string, string | number>): string {
  let url = path;
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (url.includes(`:${key}`)) {
        url = url.replace(`:${key}`, String(value));
      }
    });
  }
  return url;
}

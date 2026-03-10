import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, buildUrl } from "@shared/routes";
import { useToast } from "@/hooks/use-toast";

export function useMaterials() {
  return useQuery({
    queryKey: [api.materials.list.path],
    queryFn: async () => {
      const res = await fetch(api.materials.list.path, { credentials: "include" });
      if (!res.ok) throw new Error("Failed to fetch materials");
      return api.materials.list.responses[200].parse(await res.json());
    },
  });
}

export function useMaterial(id: number) {
  return useQuery({
    queryKey: [api.materials.get.path, id],
    queryFn: async () => {
      const url = buildUrl(api.materials.get.path, { id });
      const res = await fetch(url, { credentials: "include" });
      if (res.status === 404) return null;
      if (!res.ok) throw new Error("Failed to fetch material");
      return api.materials.get.responses[200].parse(await res.json());
    },
    enabled: !!id,
  });
}

export function useCreateMaterial() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (data: { title: string; content: string; type: string }) => {
      const res = await fetch(api.materials.create.path, {
        method: api.materials.create.method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to create material");
      return api.materials.create.responses[201].parse(await res.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [api.materials.list.path] });
      toast({ title: "Material saved successfully!" });
    },
    onError: () => {
      toast({ title: "Failed to save material", variant: "destructive" });
    }
  });
}

export function useDeleteMaterial() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (id: number) => {
      const url = buildUrl(api.materials.delete.path, { id });
      const res = await fetch(url, { method: api.materials.delete.method, credentials: "include" });
      if (!res.ok) throw new Error("Failed to delete material");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [api.materials.list.path] });
      toast({ title: "Material deleted." });
    },
  });
}

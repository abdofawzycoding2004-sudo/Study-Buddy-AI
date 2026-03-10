import { useState } from "react";
import { useMaterials, useCreateMaterial, useDeleteMaterial } from "@/hooks/use-materials";
import { Link } from "wouter";
import { motion } from "framer-motion";
import { FileText, Plus, Trash2, BookOpen, Loader2 } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useDropzone } from "react-dropzone";

export default function MaterialsPage() {
  const { data: materials, isLoading } = useMaterials();
  const deleteMutation = useDeleteMaterial();
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-8 max-w-7xl mx-auto"
    >
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-4xl font-bold font-display text-foreground mb-2">Study Materials</h1>
          <p className="text-muted-foreground text-lg">Upload notes or PDFs to build your knowledge base.</p>
        </div>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="rounded-xl px-6 py-6 shadow-lg shadow-primary/20 hover:shadow-xl hover:-translate-y-0.5 transition-all text-base gap-2">
              <Plus className="w-5 h-5" /> Add Material
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[600px] p-6 rounded-2xl">
            <DialogHeader>
              <DialogTitle className="text-2xl font-display">Add Study Material</DialogTitle>
            </DialogHeader>
            <AddMaterialForm onSuccess={() => setIsDialogOpen(false)} />
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center py-20">
          <Loader2 className="w-10 h-10 animate-spin text-primary/50" />
        </div>
      ) : materials?.length === 0 ? (
        <div className="text-center py-24 bg-card rounded-3xl border border-dashed border-border shadow-sm">
          <div className="bg-primary/5 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
            <BookOpen className="w-10 h-10 text-primary" />
          </div>
          <h3 className="text-2xl font-bold font-display mb-3">No materials yet</h3>
          <p className="text-muted-foreground max-w-sm mx-auto">Upload your first set of notes or a document to start generating quizzes and discussing with the AI.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {materials?.map((material, i) => (
            <motion.div 
              key={material.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="bg-card rounded-2xl p-6 border border-border shadow-sm hover:shadow-xl hover:border-primary/30 transition-all duration-300 group flex flex-col"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="bg-secondary p-3 rounded-xl">
                  <FileText className="w-6 h-6 text-primary" />
                </div>
                <button 
                  onClick={(e) => { e.preventDefault(); deleteMutation.mutate(material.id); }}
                  className="opacity-0 group-hover:opacity-100 p-2 text-muted-foreground hover:text-destructive transition-all rounded-lg hover:bg-destructive/10"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              
              <h3 className="text-xl font-bold font-display mb-2 line-clamp-1">{material.title}</h3>
              <p className="text-muted-foreground text-sm line-clamp-3 mb-6 flex-1">
                {material.content}
              </p>
              
              <Link href={`/materials/${material.id}`} className="block w-full text-center bg-secondary hover:bg-primary hover:text-primary-foreground text-primary font-medium py-3 rounded-xl transition-colors">
                View Material
              </Link>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
}

function AddMaterialForm({ onSuccess }: { onSuccess: () => void }) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const createMutation = useCreateMaterial();

  const onDrop = async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setTitle(file.name.replace(/\.[^/.]+$/, ""));
      const text = await file.text();
      setContent(text);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'application/pdf': ['.pdf'] // Basic text extraction fallback for MVP
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !content) return;
    createMutation.mutate({ title, content, type: "text" }, {
      onSuccess
    });
  };

  return (
    <Tabs defaultValue="upload" className="w-full mt-4">
      <TabsList className="grid grid-cols-2 mb-6">
        <TabsTrigger value="upload">Upload File</TabsTrigger>
        <TabsTrigger value="paste">Paste Text</TabsTrigger>
      </TabsList>
      
      <TabsContent value="upload" className="space-y-4">
        <div 
          {...getRootProps()} 
          className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all ${
            isDragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-secondary/50"
          }`}
        >
          <input {...getInputProps()} />
          <div className="bg-secondary w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-primary" />
          </div>
          <p className="text-lg font-medium mb-1">Drag & drop your file here</p>
          <p className="text-sm text-muted-foreground">Supports .txt, .md, .pdf</p>
        </div>
        
        {(title || content) && (
          <form onSubmit={handleSubmit} className="space-y-4 animate-in fade-in slide-in-from-bottom-4">
            <Input 
              value={title} 
              onChange={(e) => setTitle(e.target.value)} 
              placeholder="Document Title" 
              className="rounded-xl"
            />
            <Button disabled={createMutation.isPending} type="submit" className="w-full rounded-xl">
              {createMutation.isPending ? "Saving..." : "Save Material"}
            </Button>
          </form>
        )}
      </TabsContent>
      
      <TabsContent value="paste">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Title</label>
            <Input 
              value={title} 
              onChange={(e) => setTitle(e.target.value)} 
              placeholder="e.g. Biology 101 Notes" 
              className="rounded-xl"
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Content</label>
            <Textarea 
              value={content} 
              onChange={(e) => setContent(e.target.value)} 
              placeholder="Paste your study notes here..." 
              className="min-h-[200px] rounded-xl resize-y"
              required
            />
          </div>
          <Button disabled={createMutation.isPending} type="submit" className="w-full rounded-xl py-6 text-base shadow-lg shadow-primary/20 hover:shadow-xl hover:-translate-y-0.5 transition-all">
            {createMutation.isPending ? "Saving..." : "Save Material"}
          </Button>
        </form>
      </TabsContent>
    </Tabs>
  );
}

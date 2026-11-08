import { useState, useRef } from "react";
import { Upload, Sparkles, FileText } from "lucide-react";
import Button from "../UI/Button";
import Loader from "../UI/Loader";
import { parseText, parsePdf } from "../../services/api";
import type { TimelineEvent } from "../../types";

interface TextPasteInputProps {
  onEventsParsed: (events: TimelineEvent[]) => void;
}

export default function TextPasteInput({ onEventsParsed }: TextPasteInputProps) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleParseText = async () => {
    if (!text.trim()) {
      setError("Paste some text about your career first.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const result = await parseText(text);
      onEventsParsed(result.events);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to parse. Try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handlePdfUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.type !== "application/pdf") {
      setError("Please upload a PDF file.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("File too large. Maximum 10 MB.");
      return;
    }

    setError(null);
    setLoading(true);
    try {
      const result = await parsePdf(file);
      onEventsParsed(result.events);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to parse PDF. Try pasting text.";
      setError(msg);
    } finally {
      setLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  if (loading) {
    return <Loader message="Analyzing your career story with AI..." size="lg" />;
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs text-text-muted mb-2">
          Paste your resume, LinkedIn About, or describe your career story
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={`Example:\nI graduated from NIT in 2021 with 8.5 CGPA in CS. Got into Infosys campus placement. Worked there for a year, felt stuck, quit and joined a startup as backend engineer in 2022...`}
          className="w-full h-44 bg-white/[0.02] border border-white/[0.08] rounded-xl px-4 py-3 text-text text-sm placeholder-text-dim/40 focus:outline-none focus:border-primary/30 focus:ring-1 focus:ring-primary/10 resize-none transition-all"
        />
        <p className="text-[10px] text-text-dim mt-1 font-mono">
          {text.length}/10,000
        </p>
      </div>

      <div className="flex flex-col sm:flex-row gap-2.5">
        <Button onClick={handleParseText} disabled={!text.trim()} className="flex-1">
          <Sparkles className="h-3.5 w-3.5" />
          Parse & Extract Events
        </Button>

        <div className="relative flex-1">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handlePdfUpload}
            className="hidden"
          />
          <Button
            variant="secondary"
            onClick={() => fileInputRef.current?.click()}
            className="w-full"
          >
            <Upload className="h-3.5 w-3.5" />
            Upload PDF Resume
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-3 text-text-dim/30">
        <div className="flex-1 h-px bg-white/[0.04]" />
        <FileText className="h-3.5 w-3.5" />
        <span className="text-[10px]">AI extracts career events from text or PDF</span>
        <div className="flex-1 h-px bg-white/[0.04]" />
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-danger/[0.06] border border-danger/15 text-danger text-xs">
          {error}
        </div>
      )}
    </div>
  );
}

import { motion } from "framer-motion";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ExternalLink, FileText, Link2 } from "lucide-react";
import type { Source } from "@/lib/rag-types";
import { fadeUp, scaleIn } from "@/lib/motion";

export function SourceDialog({ source, onClose }: { source: Source | null; onClose: () => void }) {
  const allLinks = [
    ...(source?.url ? [source.url] : []),
    ...(source?.links?.filter((l) => l !== source?.url) ?? []),
  ];

  return (
    <Dialog open={!!source} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-2xl overflow-hidden">
        <motion.div variants={scaleIn} initial="hidden" animate="show">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 flex-wrap">
              <motion.span
                initial={{ rotate: -20, opacity: 0 }}
                animate={{ rotate: 0, opacity: 1 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <FileText className="h-4 w-4 text-mint" />
              </motion.span>
              {source?.title}
              {source?.page && (
                <span className="text-xs text-muted-foreground font-normal">· p.{source.page}</span>
              )}
            </DialogTitle>
          </DialogHeader>

          {allLinks.length > 0 && (
            <motion.div
              variants={fadeUp}
              initial="hidden"
              animate="show"
              className="mt-3 p-3 rounded-xl bg-mint-soft/30 border border-mint/20 space-y-2"
            >
              <p className="text-[11px] uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <Link2 className="h-3 w-3 text-mint" />
                Liên kết nguồn
              </p>
              {allLinks.map((link) => (
                <a
                  key={link}
                  href={link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-sm text-mint hover:underline break-all"
                >
                  <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                  {link}
                </a>
              ))}
            </motion.div>
          )}

          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate="show"
            transition={{ delay: 0.1 }}
            className="mt-3 p-4 rounded-xl bg-surface-2 border border-border max-h-[50vh] overflow-y-auto"
          >
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.4 }}
              className="text-sm leading-relaxed text-foreground/85 whitespace-pre-wrap"
            >
              {source?.excerpt}
            </motion.p>
          </motion.div>
        </motion.div>
      </DialogContent>
    </Dialog>
  );
}

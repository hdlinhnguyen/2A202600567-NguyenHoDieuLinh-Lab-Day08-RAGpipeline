import { createFileRoute } from "@tanstack/react-router";
import { PresentationSlides } from "@/components/slides/PresentationSlides";

export const Route = createFileRoute("/slide")({
  head: () => ({
    meta: [
      { title: "Arionear · Slide Thuyết trình" },
      { name: "description", content: "Slide thuyết trình RAG Pipeline Pháp luật Ma túy — Day 8" },
    ],
  }),
  component: SlidePage,
});

function SlidePage() {
  return <PresentationSlides />;
}

import { useCallback, useEffect, useRef, useState } from "react";

type SpeechOptions = {
  lang?: string;
  onFinalTranscript: (text: string) => void;
  onInterimTranscript?: (text: string) => void;
};

export function useSpeechRecognition({
  lang = "vi-VN",
  onFinalTranscript,
  onInterimTranscript,
}: SpeechOptions) {
  const [listening, setListening] = useState(false);
  const [supported, setSupported] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const callbacksRef = useRef({ onFinalTranscript, onInterimTranscript });

  useEffect(() => {
    callbacksRef.current = { onFinalTranscript, onInterimTranscript };
  }, [onFinalTranscript, onInterimTranscript]);

  useEffect(() => {
    const SR = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    setSupported(!!SR);
    if (!SR) return;

    const recognition = new SR();
    recognition.lang = lang;
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = "";
      let final = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const chunk = event.results[i][0].transcript;
        if (event.results[i].isFinal) final += chunk;
        else interim += chunk;
      }

      if (final.trim()) callbacksRef.current.onFinalTranscript(final.trim());
      callbacksRef.current.onInterimTranscript?.(interim.trim());
    };

    recognition.onerror = () => {
      setListening(false);
      setError("Không thể nhận diện giọng nói. Hãy thử lại.");
    };

    recognition.onend = () => {
      setListening(false);
      callbacksRef.current.onInterimTranscript?.("");
    };

    recognitionRef.current = recognition;
    return () => recognition.abort();
  }, [lang]);

  const start = useCallback(() => {
    if (!recognitionRef.current) {
      setError("Trình duyệt không hỗ trợ nhận diện giọng nói.");
      return;
    }
    setError(null);
    try {
      recognitionRef.current.start();
      setListening(true);
    } catch {
      setError("Microphone đang được sử dụng hoặc chưa được cấp quyền.");
      setListening(false);
    }
  }, []);

  const stop = useCallback(() => {
    recognitionRef.current?.stop();
    setListening(false);
    callbacksRef.current.onInterimTranscript?.("");
  }, []);

  const toggle = useCallback(() => {
    if (listening) stop();
    else start();
  }, [listening, start, stop]);

  return { listening, supported, error, start, stop, toggle, clearError: () => setError(null) };
}

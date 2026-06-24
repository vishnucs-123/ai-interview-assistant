"""
Answer Generation Engine.
Takes a detected question and generates a concise interview answer
using a local LLM via Ollama. Completely offline — no API calls.
"""

import ollama
from dataclasses import dataclass
from backend.transcriber.question_detector import DetectedQuestion
from backend.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class GeneratedAnswer:
    question: str
    answer: str
    category: str
    topic: str
    model_used: str

    def __str__(self):
        return (
            f"\n{'='*60}\n"
            f"Q [{self.category} | {self.topic}]: {self.question}\n"
            f"{'-'*60}\n"
            f"A: {self.answer}\n"
            f"{'='*60}"
        )


PROMPTS = {
    "Technical": """You are an expert Java Full Stack Developer in a technical interview.
Answer the following technical question concisely and clearly.
- Keep answer under 120 words
- Use bullet points where helpful
- Include a short code example only if essential

Question: {question}

Answer:""",

    "Behavioral": """You are a software engineer in a behavioral interview.
Answer using the STAR method (Situation, Task, Action, Result).
- Keep answer under 150 words
- Be specific and professional

Question: {question}

Answer:""",

    "Coding": """You are a software engineer solving a coding interview problem.
Provide:
1. Approach (1-2 sentences)
2. Time Complexity
3. Space Complexity
4. Java code solution
5. One edge case

Question: {question}

Answer:""",

    "System Design": """You are a senior software engineer in a system design interview.
- Mention key components
- Discuss scalability briefly
- Keep answer under 150 words

Question: {question}

Answer:""",

    "HR": """You are a software engineering candidate in an HR interview.
Answer professionally and positively in under 100 words.

Question: {question}

Answer:""",

    "General": """You are a software engineering candidate in a job interview.
Answer concisely and professionally in under 120 words.

Question: {question}

Answer:""",
}


class AnswerEngine:
    """
    Generates interview answers using a local Ollama LLM.
    """

    def __init__(self, model: str = "llama3.2"):
        self.model = model
        logger.info(f"AnswerEngine initialized | model={model}")

    def check_ollama_running(self) -> bool:
        """
        Check if Ollama is running and the model is available.
        Works with all ollama Python package versions.
        """
        try:
            response = ollama.list()

            # response is an object, not a dict in newer versions
            # try attribute access first, then dict access
            try:
                model_list = response.models  # newer ollama versions
            except AttributeError:
                model_list = response.get("models", [])  # older versions

            available = []
            for m in model_list:
                # each model may be an object or dict
                try:
                    name = m.model  # newer: attribute access
                except AttributeError:
                    name = m.get("model") or m.get("name") or str(m)
                available.append(name)

            logger.info(f"Available Ollama models: {available}")

            if not any(self.model in m for m in available):
                logger.warning(
                    f"Model '{self.model}' not found locally. "
                    f"Run: ollama pull {self.model}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Ollama connection failed: {e}")
            return False

    def generate(self, detected_question: DetectedQuestion) -> GeneratedAnswer:
        """
        Generate an answer for a detected interview question.
        """
        if not detected_question.is_question:
            return GeneratedAnswer(
                question=detected_question.text,
                answer="(Not detected as a question — no answer generated)",
                category=detected_question.category,
                topic=detected_question.topic,
                model_used=self.model
            )

        prompt = self._build_prompt(detected_question)

        logger.info(
            f"Generating answer | "
            f"category={detected_question.category} | "
            f"topic={detected_question.topic}"
        )

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )

            # Handle both object and dict response formats
            try:
                answer = response.message.content.strip()  # newer versions
            except AttributeError:
                answer = response["message"]["content"].strip()  # older versions

        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            answer = f"[Error: {e}]"

        result = GeneratedAnswer(
            question=detected_question.text,
            answer=answer,
            category=detected_question.category,
            topic=detected_question.topic,
            model_used=self.model
        )

        logger.info("Answer generated successfully")
        return result

    def generate_from_text(self, text: str) -> GeneratedAnswer:
        """Convenience method — detect question and generate answer in one call."""
        from backend.transcriber.question_detector import QuestionDetector
        detector = QuestionDetector()
        detected = detector.detect(text)
        return self.generate(detected)

    def _build_prompt(self, question: DetectedQuestion) -> str:
        """Select the right prompt template based on question category."""
        template = PROMPTS.get(question.category, PROMPTS["General"])
        return template.format(question=question.text)
    
    def generate_with_resume(
        self,
        detected_question,
        resume_context: str = "",
        memory_context: str = ""
    ):
        """
        Generate answer with resume + memory context injected.
        Makes answers personalized to the candidate's actual experience.
        """
        from backend.transcriber.question_detector import DetectedQuestion

        if not detected_question.is_question:
            return self.generate(detected_question)

        # Build enriched prompt with both contexts
        base_template = PROMPTS.get(
            detected_question.category, PROMPTS["General"]
        )

        extra_context = ""
        if resume_context:
            extra_context += f"\n\n{resume_context}"
        if memory_context:
            extra_context += f"\n\n{memory_context}"

        enriched_prompt = base_template.format(
            question=detected_question.text
        ) + extra_context

        logger.info(
            f"Generating answer with RAG context | "
            f"resume_chunks={bool(resume_context)} | "
            f"memory={bool(memory_context)}"
        )

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": enriched_prompt}]
            )
            try:
                answer = response.message.content.strip()
            except AttributeError:
                answer = response["message"]["content"].strip()

        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            answer = f"[Error: {e}]"

        from backend.llm.answer_engine import GeneratedAnswer
        return GeneratedAnswer(
            question=detected_question.text,
            answer=answer,
            category=detected_question.category,
            topic=detected_question.topic,
            model_used=self.model
        )
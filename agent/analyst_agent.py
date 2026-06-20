import logging
import os
import re
from typing import Optional
from agent.langchain_agent import LangChainAnalystAgent
from tools.dataset_tools import get_dataset_schema, get_missing_values
from tools.plotting_tools import build_histograms, build_correlation_heatmap
from reports.report_builder import build_report_data
from reports.pdf_builder import create_pdf_report

logger = logging.getLogger(__name__)


class AnalystAgent:
    """LangChain агент с поддержкой PDF отчета"""

    def __init__(self):
        self.langchain_agent = LangChainAnalystAgent()
        self.df = None
        self.generated_plots = []

    def sanitize_instruction(self, instruction: str) -> str:
        """Защита от prompt-injection"""
        if not instruction:
            return ""

        # Список опасных паттернов
        dangerous_patterns = [
            r"ignore previous instructions",
            r"forget your role",
            r"you are now",
            r"system prompt",
            r"new instructions",
            r"override",
            r"disregard",
            r"developer message",
            r"reveal prompt",
            r"you are an ai",
            r"you are a language model",
            r"you are chatgpt",
            r"you are gpt",
            r"pretend to be",
            r"act as",
            r"roleplay",
            r"jailbreak",
            r"bypass",
            r"system:",
            r"developer:",
            r"assistant:",
            r"user:",
            r"<|im_start|>",
            r"<|im_end|>",
        ]

        sanitized = instruction
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        # Удаление попыток экранирования
        sanitized = re.sub(r'\\', '', sanitized)
        sanitized = re.sub(r'\{.*?\}', '', sanitized)

        # Ограничение длины
        return sanitized[:5000].strip()

    def analyze(self, file_path: str, instruction: Optional[str] = None):
        """Запуск анализа данных через LangChain агента."""
        logger.info(f"Начало анализа: {file_path}")

        # Защита от prompt-injection
        safe_instruction = self.sanitize_instruction(instruction or "")

        try:
            # Запуск LangChain агента
            result = self.langchain_agent.analyze(file_path, safe_instruction)

            # Сохранение данных для отчета
            self.df = self.langchain_agent.df
            self.generated_plots = result.get("plots", [])
            llm_report = result.get("report", "Анализ завершен")

            # Создание PDF отчета
            pdf_path = self.build_final_pdf(llm_report)

            logger.info(f"Отчет создан: {pdf_path}")
            return pdf_path

        except Exception as e:
            logger.error(f"Ошибка при анализе: {e}")
            raise

    def build_final_pdf(self, llm_report: str) -> str:
        """Создание PDF отчета с анализом и визуализациями."""

        import re

        # Очищение отчета от лишних символов
        clean_report = re.sub(r'\*\*(.*?)\*\*', r'\1', llm_report)
        clean_report = re.sub(r'\*(.*?)\*', r'\1', clean_report)
        clean_report = re.sub(r'#{1,6}\s*', '', clean_report)
        clean_report = clean_report.replace('***', '')
        clean_report = clean_report.replace('**', '')
        clean_report = clean_report.replace('*', '')

        # Информация о датасете
        dataset_schema = get_dataset_schema(self.df)
        dataset_schema['missing_values'] = get_missing_values(self.df)

        # Убираем дубликаты графиков
        unique_plots = []
        seen = set()
        for plot in self.generated_plots:
            if plot not in seen:
                unique_plots.append(plot)
                seen.add(plot)

        # Данные для отчета
        report_data = build_report_data(
            dataset_info=dataset_schema,
            llm_report=clean_report,  # Очищенный отчет
            plots=unique_plots  # Уникальные графики
        )

        # Создание PDF
        os.makedirs("generated/reports", exist_ok=True)
        pdf_path = "generated/reports/analysis_report.pdf"
        create_pdf_report(report_data, pdf_path)

        return pdf_path
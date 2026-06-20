from datetime import datetime
import re


def clean_text(text: str) -> str:
    """Очищает текст от Markdown и лишних символов"""
    if not text:
        return ""

    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'#{1,6}\s*', '', text)
    text = text.replace('***', '')
    text = text.replace('**', '')
    text = text.replace('*', '')

    return text.strip()


def build_report_data(
        dataset_info,
        llm_report,
        plots
):
    # Очистка отчета перед сохранением
    clean_report = clean_text(llm_report)

    return {
        "created_at": datetime.now(),
        "dataset_info": dataset_info,
        "analysis": clean_report,
        "plots": plots
    }
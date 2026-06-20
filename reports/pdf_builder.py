import re
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def clean_markdown(text: str) -> str:
    """Очищение текста от разметки и лишних символов"""
    if not text:
        return ""

    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'^[\s]*[-*]\s+', '• ', text, flags=re.MULTILINE)
    text = re.sub(r'^[\s]*\d+\.\s+', '• ', text, flags=re.MULTILINE)
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('***', '')
    text = text.replace('**', '')
    text = text.replace('*', '')
    text = text.replace('_', '')
    text = re.sub(r'[^\w\s.,!?;:()\-—«»""\'"]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def create_pdf_report(report_data, output_path):
    """Создание PDF отчета"""

    # Шрифты
    try:
        pdfmetrics.registerFont(TTFont("DejaVuSans", "fonts/DejaVuSans.ttf"))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", "fonts/DejaVuSans-Bold.ttf"))
    except:
        # Если шрифты не найдены, используем стандартные
        print("Warning: Шрифты DejaVu не найдены, используем стандартные")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    styles = getSampleStyleSheet()

    # Настройка стилей
    try:
        styles["Normal"].fontName = "DejaVuSans"
        styles["Title"].fontName = "DejaVuSans-Bold"
        styles["Heading1"].fontName = "DejaVuSans-Bold"
        styles["Heading2"].fontName = "DejaVuSans-Bold"
    except:
        pass

    styles.add(ParagraphStyle(
        name='Justify',
        parent=styles['Normal'],
        fontName='DejaVuSans',
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
    ))

    styles.add(ParagraphStyle(
        name='Centered',
        parent=styles['Normal'],
        fontName='DejaVuSans',
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
    ))

    story = []

    # Заголовок
    story.append(Paragraph("Отчет по анализу данных", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Сгенерировано AI Аналитиком", styles["Heading2"]))
    story.append(Spacer(1, 20))

    # Информация о датасете
    dataset_info = report_data["dataset_info"]

    story.append(Paragraph("Обзор датасета", styles["Heading1"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"Количество строк: {dataset_info['rows']}", styles["Normal"]))
    story.append(Paragraph(f"Количество столбцов: {dataset_info['columns']}", styles["Normal"]))
    story.append(Spacer(1, 6))

    # Названия столбцов
    story.append(Paragraph("Названия столбцов:", styles["Normal"]))
    cols = dataset_info['column_names']
    for i in range(0, len(cols), 2):
        line = f"• {cols[i]}"
        if i + 1 < len(cols):
            line += f" • {cols[i + 1]}"
        story.append(Paragraph(line, styles["Normal"]))
    story.append(Spacer(1, 6))

    # Типы данных
    story.append(Paragraph("Типы данных:", styles["Normal"]))
    dtypes = dataset_info['dtypes']
    items = list(dtypes.items())
    for i in range(0, len(items), 2):
        line = f"• {items[i][0]}: {items[i][1]}"
        if i + 1 < len(items):
            line += f" • {items[i + 1][0]}: {items[i + 1][1]}"
        story.append(Paragraph(line, styles["Normal"]))
    story.append(Spacer(1, 6))

    # Пропущенные значения
    if 'missing_values' in dataset_info:
        story.append(Paragraph("Пропущенные значения:", styles["Normal"]))
        missing = dataset_info['missing_values']
        for col, info in missing.items():
            if info.get('count', 0) > 0:
                story.append(Paragraph(
                    f"• {col}: {info['count']} пропущенных ({info['percent']}%)",
                    styles["Normal"]
                ))
            else:
                story.append(Paragraph(
                    f"• {col}: Нет пропущенных значений",
                    styles["Normal"]
                ))

    story.append(PageBreak())

    # Анализ
    story.append(Paragraph("Анализ данных", styles["Heading1"]))
    story.append(Spacer(1, 12))

    # Очистка текста
    analysis_text = report_data["analysis"]
    analysis_text = clean_markdown(analysis_text)

    paragraphs = analysis_text.split('\n\n')

    for para in paragraphs:
        if para.strip():
            # Проверка, является ли это заголовком
            if para.strip().endswith(':') or len(para.strip()) < 60:
                # Очистка от лишних символов
                clean_para = para.strip().replace(':', '')
                story.append(Paragraph(clean_para, styles["Heading2"]))
            else:
                story.append(Paragraph(para.strip(), styles["Justify"]))
            story.append(Spacer(1, 6))

    story.append(PageBreak())

    # Визуализации
    if report_data["plots"]:
        story.append(Paragraph("Визуализации", styles["Heading1"]))
        story.append(Spacer(1, 12))

        # Уникальные графики
        unique_plots = []
        seen = set()
        for plot_path in report_data["plots"]:
            if plot_path not in seen:
                unique_plots.append(plot_path)
                seen.add(plot_path)

        plots_to_show = unique_plots[:8]

        for plot_path in plots_to_show:
            if os.path.exists(plot_path):
                try:
                    # Имя файла для подписи
                    plot_name = os.path.basename(plot_path).replace('.png', '').replace('_', ' ').title()

                    plot_name_ru = plot_name
                    if 'Hist' in plot_name:
                        plot_name_ru = plot_name.replace('Hist', 'Гистограмма')
                    elif 'Heatmap' in plot_name:
                        plot_name_ru = plot_name.replace('Heatmap', 'Тепловая карта корреляций')
                    elif 'Correlation' in plot_name:
                        plot_name_ru = plot_name.replace('Correlation', 'Корреляция')
                    elif 'Box' in plot_name:
                        plot_name_ru = plot_name.replace('Box', 'Boxplot')
                    elif 'Scatter' in plot_name:
                        plot_name_ru = plot_name.replace('Scatter', 'Диаграмма рассеяния')

                    story.append(Paragraph(f"{plot_name_ru}", styles["Heading2"]))
                    story.append(Spacer(1, 6))

                    img = Image(plot_path, width=450, height=300)
                    story.append(img)
                    story.append(Spacer(1, 20))

                except Exception as e:
                    print(f"Error adding image {plot_path}: {e}")

    try:
        doc.build(story)
        return output_path
    except Exception as e:
        print(f"Error building PDF: {e}")
        raise
import json
import logging
import os
from typing import Dict, Any, Optional, List

from langchain_classic.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool, StructuredTool

from tools.dataset_tools import (
    load_dataset,
    get_dataset_schema,
    sample_dataset,
    get_missing_values,
    get_numeric_summary,
    get_categorical_summary,
    get_correlations,
    detect_outliers,
)
from tools.python_executor import execute_python_on_df
from tools.plotting_tools import create_plot, build_histograms, build_correlation_heatmap

logger = logging.getLogger(__name__)


class LangChainAnalystAgent:
    """Агент для анализа данных с использованием OpenAI Functions"""

    def __init__(self):
        self.df = None
        self.tools = []
        self.agent_executor = None
        self.generated_plots = []
        self.analysis_history = []
        self.step_count = 0

        # Инициализация LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            base_url="https://api.aitunnel.ru/v1/",
            api_key=os.getenv("API_KEY"),
            temperature=0.1,
            timeout=200.0,
            max_retries=2,
            default_headers={"Accept-Language": "ru"}
        )

        logger.info(f"Инициализирован LLM: gpt-4o-mini")

    def _create_tools(self):
        """Создание инструментов"""

        tools = []

        # get_schema
        tools.append(StructuredTool.from_function(
            func=lambda: json.dumps(get_dataset_schema(self.df), ensure_ascii=False, default=str),
            name="get_schema",
            description="Получить структуру датасета: количество строк, столбцов, типы данных. Не требует параметров."
        ))

        # sample_data
        tools.append(StructuredTool.from_function(
            func=lambda rows=5: json.dumps(sample_dataset(self.df, rows), ensure_ascii=False, default=str),
            name="sample_data",
            description="Получить случайную выборку строк из датасета. rows - количество строк (по умолчанию 5)"
        ))

        # get_missing
        tools.append(StructuredTool.from_function(
            func=lambda: json.dumps(get_missing_values(self.df), ensure_ascii=False, default=str),
            name="get_missing",
            description="Получить информацию о пропущенных значениях. Не требует параметров."
        ))

        # get_numeric_stats
        tools.append(StructuredTool.from_function(
            func=lambda: json.dumps(get_numeric_summary(self.df), ensure_ascii=False, default=str),
            name="get_numeric_stats",
            description="Получить статистику числовых признаков. Не требует параметров."
        ))

        # get_categorical_stats
        tools.append(StructuredTool.from_function(
            func=lambda: json.dumps(get_categorical_summary(self.df), ensure_ascii=False, default=str),
            name="get_categorical_stats",
            description="Получить статистику категориальных признаков. Не требует параметров."
        ))

        # get_correlations
        tools.append(StructuredTool.from_function(
            func=lambda: json.dumps(get_correlations(self.df), ensure_ascii=False, default=str),
            name="get_correlations",
            description="Получить корреляционную матрицу. Не требует параметров."
        ))

        # detect_outliers
        tools.append(StructuredTool.from_function(
            func=lambda: json.dumps(detect_outliers(self.df), ensure_ascii=False, default=str),
            name="detect_outliers",
            description="Обнаружить выбросы в данных. Не требует параметров."
        ))

        # execute_python
        def execute_python_func(code: str):
            if len(code) > 2000:
                return "Код слишком длинный."
            return execute_python_on_df(code, self.df)

        tools.append(StructuredTool.from_function(
            func=execute_python_func,
            name="execute_python",
            description="Выполнить Python код для анализа данных. Доступны переменные: df (DataFrame), pd, np. code - строка с Python кодом"
        ))

        # create_visualization
        def create_visualization_func(plot_type: str, column: str, x_column: str = None, y_column: str = None):
            try:
                result = create_plot(
                    df=self.df,
                    plot_type=plot_type,
                    output_dir="generated/plots",
                    column=column,
                    x_column=x_column,
                    y_column=y_column
                )
                if result and "saved:" in result:
                    path = result.split("saved: ")[1].strip()
                    self.generated_plots.append(path)
                return result
            except Exception as e:
                return f"Ошибка создания визуализации: {e}"

        tools.append(StructuredTool.from_function(
            func=create_visualization_func,
            name="create_visualization",
            description="""Создать визуализацию данных.
            plot_type: тип графика (hist, box, scatter, bar)
            column: название колонки для гистограммы/boxplot/bar
            x_column: колонка для оси X (для scatter)
            y_column: колонка для оси Y (для scatter)"""
        ))

        return tools

    def _create_agent(self):
        """Создание агента с OpenAI Functions"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Необходимо провести глубокий анализ датасета.

Правила работы:
1. Используй инструменты для получения данных
2. Проведи полный анализ: структура, статистика, корреляции, выбросы
3. Используй execute_python для сложных вычислений
4. Создай минимум 5 визуализаций через create_visualization
5. Сделай 5-7 ключевых вывода с конкретными цифрами

План анализа:
1. get_schema() - структура данных
2. sample_data(5) - примеры записей
3. get_missing() - пропуски
4. get_numeric_stats() - числовая статистика
5. get_categorical_stats() - категориальная статистика
6. get_correlations() - корреляции
7. detect_outliers() - выбросы
8. execute_python() - группировки, тренды, распределения
9. create_visualization() - создание графиков

После сбора всех данных предоставь структурированный отчет на русском языке."""),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=25,
            max_execution_time=180,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )

        return agent_executor

    def analyze(self, file_path: str, instruction: Optional[str] = None) -> Dict[str, Any]:
        """Запуск анализа данных через агента"""

        logger.info(f"Загрузка датасета: {file_path}")
        self.df = load_dataset(file_path)
        logger.info(f"Датасет загружен: {len(self.df)} строк, {len(self.df.columns)} колонок")
        logger.info(f"Колонки: {list(self.df.columns)}")

        # Создание инструментов и агента
        self.tools = self._create_tools()
        logger.info(f"Создано {len(self.tools)} инструментов")

        self.agent_executor = self._create_agent()

        task = f"""Проведи глубокий исследовательский анализ данных.

Обязательно выполни все шаги:
1. Вызови get_schema() - узнай структуру
2. Вызови sample_data(5) - посмотри на данные
3. Вызови get_missing() - проверь пропуски
4. Вызови get_numeric_stats() - получи статистику
5. Вызови get_categorical_stats() - получи статистику категорий
6. Вызови get_correlations() - найди корреляции
7. Вызови detect_outliers() - найди выбросы
8. Используй execute_python() для группировок и трендов
9. Создай минимум 5 графиков через create_visualization()

{f"Инструкция пользователя: {instruction}" if instruction else ""}

После выполнения всех шагов предоставь подробный отчет на русском языке."""

        logger.info("Запуск агента...")

        try:
            result = self.agent_executor.invoke({
                "input": task
            })

            self.analysis_history = result.get("intermediate_steps", [])
            llm_report = result.get("output", "Анализ завершен")

            # Проверка количества графиков
            if len(self.generated_plots) < 4:
                logger.info("Автоматическое создание дополнительных графиков...")
                histograms = build_histograms(self.df, "generated/plots")
                self.generated_plots.extend(histograms)

                heatmap = build_correlation_heatmap(self.df, "generated/plots")
                if heatmap:
                    self.generated_plots.append(heatmap)

            return {
                "report": llm_report,
                "plots": self.generated_plots,
                "history": self.analysis_history
            }

        except Exception as e:
            logger.error(f"Ошибка при выполнении агента: {e}")
            return self._fallback_analysis()

    def _fallback_analysis(self) -> Dict[str, Any]:
        """Прямой анализ без агента (если агент не работает)"""
        logger.info("Использование прямого анализа")

        # Получение данных через инструменты
        schema = get_dataset_schema(self.df)
        missing = get_missing_values(self.df)
        numeric_stats = get_numeric_summary(self.df)
        categorical_stats = get_categorical_summary(self.df)
        correlations = get_correlations(self.df)
        outliers = detect_outliers(self.df)

        # Построение графиков
        histograms = build_histograms(self.df, "generated/plots")
        self.generated_plots.extend(histograms[:5])
        heatmap = build_correlation_heatmap(self.df, "generated/plots")
        if heatmap:
            self.generated_plots.append(heatmap)

        # Формирование отчета
        report_parts = []
        report_parts.append("Отчет по анализу датасета\n")

        # 1. Структура данных
        report_parts.append("\nСтруктура данных:")
        report_parts.append(f"• Строк: {schema['rows']}")
        report_parts.append(f"• Столбцов: {schema['columns']}")
        report_parts.append("• Колонки: " + ", ".join(schema['column_names']))
        report_parts.append(f"• Типы данных: {json.dumps(schema['dtypes'], ensure_ascii=False)}")

        # 2. Пропуски
        if missing:
            report_parts.append("\nПропущенные значения:")
            missing_cols = [col for col, info in missing.items() if info['count'] > 0]
            if missing_cols:
                for col in missing_cols[:5]:
                    report_parts.append(f"• {col}: {missing[col]['count']} ({missing[col]['percent']}%)")
            else:
                report_parts.append("• Пропущенных значений нет")

        # 3. Числовая статистика
        if numeric_stats:
            report_parts.append("\nЧисловая статистика:")
            for col, stats in list(numeric_stats.items())[:5]:
                report_parts.append(f"\n• {col}:")
                for key, value in stats.items():
                    if isinstance(value, (int, float)):
                        report_parts.append(f"  - {key}: {value:.2f}")
                    else:
                        report_parts.append(f"  - {key}: {value}")

        # 4. Категориальная статистика
        if categorical_stats:
            report_parts.append("\nКатегориальная статистика:")
            for col, stats in list(categorical_stats.items())[:5]:
                report_parts.append(f"• {col}: {stats['unique']} уникальных значений")
                if stats['top_values']:
                    report_parts.append("  Топ-5:")
                    for val, count in list(stats['top_values'].items())[:5]:
                        report_parts.append(f"    - {val}: {count}")

        # 5. Корреляции
        if correlations:
            report_parts.append("\nКорреляции:")
            for corr in correlations[:5]:
                report_parts.append(
                    f"• {corr['column_1']} - {corr['column_2']}: "
                    f"{corr['correlation']:.3f}"
                )

        # 6. Выбросы
        if outliers:
            report_parts.append("\nВыбросы:")
            outlier_cols = [col for col, count in outliers.items() if count > 0]
            if outlier_cols:
                for col in outlier_cols[:5]:
                    report_parts.append(f"• {col}: {outliers[col]} выбросов")
            else:
                report_parts.append("• Выбросов не обнаружено")

        # 7. Выводы
        report_parts.append("\nВыводы:")
        insights = []

        if numeric_stats:
            max_std_col = max(numeric_stats.items(), key=lambda x: x[1].get('std', 0))
            if max_std_col[1].get('std', 0) > 0:
                insights.append(f"• Наибольший разброс данных в колонке '{max_std_col[0]}': стандартное отклонение = {max_std_col[1]['std']:.2f}")

        if correlations:
            strongest = max(correlations, key=lambda x: abs(x['correlation']))
            if abs(strongest['correlation']) > 0.7:
                insights.append(f"• Обнаружена сильная корреляция ({strongest['correlation']:.3f}) между '{strongest['column_1']}' и '{strongest['column_2']}'")

        if outliers:
            total_outliers = sum(outliers.values())
            if total_outliers > 0:
                insights.append(f"• В данных обнаружено {total_outliers} выбросов, которые могут содержать важную информацию")

        if missing:
            missing_count = sum(info['count'] for info in missing.values())
            if missing_count > 0:
                insights.append(f"• Обнаружено {missing_count} пропущенных значений, требуется их обработка")

        if not insights:
            insights.append("• Данные не содержат явных аномалий")
            insights.append("• Рекомендуется провести дополнительный анализ")

        report_parts.extend(insights)

        # 8. Рекомендации
        report_parts.append("\nРекомендации:")
        recommendations = []

        if any(info['count'] > 0 for info in missing.values()):
            recommendations.append("• Заполните пропущенные значения или удалите строки с пропусками")

        if correlations:
            recommendations.append("• Используйте выявленные корреляции для прогнозирования")

        if outliers and total_outliers > 0:
            recommendations.append("• Проанализируйте выбросы отдельно - они могут содержать важные бизнес-инсайты")

        recommendations.append("• Рассмотрите возможность создания дополнительных визуализаций")
        recommendations.append("• Проверьте данные на дубликаты и ошибки ввода")

        report_parts.extend(recommendations)

        return {
            "report": "\n".join(report_parts),
            "plots": self.generated_plots,
            "history": []
        }
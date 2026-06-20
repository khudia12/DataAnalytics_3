import os
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


def build_histograms(df, output_dir):
    """Гистограммы для числовых колонок"""
    os.makedirs(output_dir, exist_ok=True)

    numeric_columns = df.select_dtypes(include=["number"]).columns
    generated = []

    for column in numeric_columns:
        try:
            plt.figure(figsize=(10, 6))

            # Убираем выбросы
            data = df[column].dropna()
            if len(data) > 0:
                sns.histplot(data, kde=True, bins=30)
                plt.title(f'Distribution of {column}')
                plt.xlabel(column)
                plt.ylabel('Frequency')
                plt.grid(True, alpha=0.3)

                file_path = os.path.join(output_dir, f"{column}_hist.png")
                plt.savefig(file_path, dpi=100, bbox_inches='tight')
                plt.close()

                generated.append(file_path)
        except Exception as e:
            print(f"Error creating histogram for {column}: {e}")
            plt.close()

    return generated


def build_correlation_heatmap(df, output_dir):
    """Тепловая карта корреляций"""
    numeric_df = df.select_dtypes(include=["number"])

    if numeric_df.shape[1] < 2:
        return None

    try:
        plt.figure(figsize=(12, 10))

        corr_matrix = numeric_df.corr()
        sns.heatmap(
            corr_matrix,
            annot=True,
            fmt='.2f',
            cmap='coolwarm',
            center=0,
            square=True,
            cbar_kws={"shrink": 0.8}
        )
        plt.title('Correlation Heatmap')

        file_path = os.path.join(output_dir, "correlation_heatmap.png")
        plt.savefig(file_path, dpi=100, bbox_inches='tight')
        plt.close()

        return file_path
    except Exception as e:
        print(f"Error creating heatmap: {e}")
        plt.close()
        return None


def create_plot(
        df,
        plot_type,
        output_dir,
        column,
        x_column=None,
        y_column=None
):
    """График по запросу"""
    os.makedirs(output_dir, exist_ok=True)

    if column not in df.columns:
        return f"Column '{column}' not found in dataset"

    try:
        plt.figure(figsize=(10, 6))

        if plot_type == "hist":
            sns.histplot(df[column].dropna(), kde=True, bins=30)
            plt.title(f'Histogram of {column}')
            plt.xlabel(column)
            plt.ylabel('Frequency')

        elif plot_type == "box":
            sns.boxplot(y=df[column])
            plt.title(f'Box Plot of {column}')
            plt.ylabel(column)

        elif plot_type == "scatter":
            if not x_column or not y_column:
                return "Scatter requires x_column and y_column"

            plt.scatter(
                df[x_column],
                df[y_column]
            )

            plt.xlabel(x_column)
            plt.ylabel(y_column)

        elif plot_type == "bar":
            if df[column].dtype == 'object':
                value_counts = df[column].value_counts().head(20)
                plt.bar(value_counts.index, value_counts.values)
                plt.title(f'Bar Chart of {column}')
                plt.xlabel(column)
                plt.ylabel('Count')
                plt.xticks(rotation=45)
            else:
                return "Bar chart requires categorical column"
        else:
            return f"Unsupported plot type: {plot_type}"

        plt.grid(True, alpha=0.3)

        file_path = os.path.join(output_dir, f"{column}_{plot_type}.png")
        plt.savefig(file_path, dpi=100, bbox_inches='tight')
        plt.close()

        return f"Plot saved: {file_path}"

    except Exception as e:
        plt.close()
        return f"Error creating plot: {e}"
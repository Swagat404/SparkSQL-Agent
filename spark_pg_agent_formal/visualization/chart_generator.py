import pandas as pd
import numpy as np
import json
from typing import Dict, List, Any, Tuple, Optional
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.figure import Figure

class ChartGenerator:
    """
    Generate and suggest appropriate chart visualizations for query results.
    """
    
    def __init__(self):
        """Initialize the chart generator."""
        self.chart_types = [
            "bar", "line", "scatter", "pie", "histogram", 
            "heatmap", "box", "area", "bubble"
        ]
    
    def _analyze_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze a DataFrame to determine appropriate visualization types.
        
        Args:
            df: The DataFrame to analyze
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": {},
            "numeric_columns": [],
            "categorical_columns": [],
            "datetime_columns": [],
            "text_columns": [],
            "uniqueness": {},
            "null_counts": {},
            "correlations": None
        }
        
        # Skip analysis if DataFrame is empty
        if df.empty:
            return analysis
        
        # Analyze each column
        for col in df.columns:
            col_type = str(df[col].dtype)
            unique_count = df[col].nunique()
            uniqueness_ratio = unique_count / len(df) if len(df) > 0 else 0
            null_count = df[col].isna().sum()
            
            analysis["columns"][col] = {
                "dtype": col_type,
                "unique_count": unique_count,
                "uniqueness_ratio": uniqueness_ratio,
                "null_count": null_count
            }
            
            analysis["uniqueness"][col] = uniqueness_ratio
            analysis["null_counts"][col] = null_count
            
            # Categorize columns
            if pd.api.types.is_numeric_dtype(df[col]):
                analysis["numeric_columns"].append(col)
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                analysis["datetime_columns"].append(col)
            elif uniqueness_ratio < 0.2 or unique_count < 20:
                # Low cardinality columns likely categorical
                analysis["categorical_columns"].append(col)
            else:
                # High cardinality, likely text data
                analysis["text_columns"].append(col)
        
        # Calculate correlations between numeric columns
        if len(analysis["numeric_columns"]) > 1:
            try:
                corr_matrix = df[analysis["numeric_columns"]].corr()
                analysis["correlations"] = corr_matrix.to_dict()
            except Exception:
                # Some numeric columns might not be suitable for correlation
                pass
        
        return analysis
    
    def _suggest_charts(self, analysis: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """
        Suggest appropriate chart types based on data analysis.
        
        Args:
            analysis: DataFrame analysis
            query: The original query
            
        Returns:
            List of suggested chart configurations
        """
        suggestions = []
        
        if len(analysis["numeric_columns"]) == 0:
            # No numeric data, limited options
            return suggestions
        
        # Look for time series data
        time_cols = analysis["datetime_columns"]
        if time_cols and analysis["numeric_columns"]:
            for time_col in time_cols:
                for metric in analysis["numeric_columns"][:3]:  # Limit to first 3 metrics
                    suggestions.append({
                        "type": "line",
                        "title": f"{metric.capitalize()} over time",
                        "x_axis": time_col,
                        "y_axis": metric,
                        "description": f"Time series showing {metric} trends over {time_col}",
                        "score": 0.9
                    })
        
        # Bar charts for categorical data
        if analysis["categorical_columns"] and analysis["numeric_columns"]:
            for cat_col in analysis["categorical_columns"][:2]:  # Limit to first 2 categories
                for metric in analysis["numeric_columns"][:2]:  # Limit to first 2 metrics
                    suggestions.append({
                        "type": "bar",
                        "title": f"{metric.capitalize()} by {cat_col}",
                        "x_axis": cat_col,
                        "y_axis": metric,
                        "description": f"Bar chart comparing {metric} across different {cat_col} values",
                        "score": 0.8
                    })
        
        # Pie charts for categorical with small number of values
        for cat_col in analysis["categorical_columns"]:
            if analysis["columns"][cat_col]["unique_count"] <= 8:
                for metric in analysis["numeric_columns"][:1]:
                    suggestions.append({
                        "type": "pie",
                        "title": f"Distribution of {metric} by {cat_col}",
                        "values": metric,
                        "labels": cat_col,
                        "description": f"Pie chart showing distribution of {metric} across {cat_col} categories",
                        "score": 0.7
                    })
        
        # Scatter plots for correlated variables
        if analysis["correlations"] and len(analysis["numeric_columns"]) >= 2:
            # Get top 2 most correlated columns
            corr_matrix = pd.DataFrame(analysis["correlations"])
            # Remove self-correlations
            for col in corr_matrix.columns:
                corr_matrix.at[col, col] = 0
            
            # Find highest correlation
            max_corr = 0
            col1, col2 = None, None
            
            for c1 in corr_matrix.columns:
                for c2 in corr_matrix.index:
                    if abs(corr_matrix.at[c2, c1]) > max_corr:
                        max_corr = abs(corr_matrix.at[c2, c1])
                        col1, col2 = c1, c2
            
            if col1 and col2 and max_corr > 0.5:
                suggestions.append({
                    "type": "scatter",
                    "title": f"Correlation between {col1} and {col2}",
                    "x_axis": col1,
                    "y_axis": col2,
                    "description": f"Scatter plot showing relationship between {col1} and {col2} (correlation: {max_corr:.2f})",
                    "score": 0.85
                })
        
        # Histograms for numeric columns with enough distinct values
        for col in analysis["numeric_columns"]:
            if analysis["columns"][col]["unique_count"] > 10:
                suggestions.append({
                    "type": "histogram",
                    "title": f"Distribution of {col}",
                    "values": col,
                    "description": f"Histogram showing the distribution of values for {col}",
                    "score": 0.75
                })
        
        # Sort suggestions by score
        suggestions = sorted(suggestions, key=lambda x: x["score"], reverse=True)
        
        # Adjust scores based on query keywords
        query_lower = query.lower()
        keywords = {
            "trend": ["line", "area"],
            "over time": ["line", "area"],
            "distribution": ["histogram", "pie"],
            "compare": ["bar", "column"],
            "correlation": ["scatter", "heatmap"],
            "relationship": ["scatter"],
            "breakdown": ["pie", "bar"],
            "composition": ["pie", "stacked"],
            "geographic": ["map"],
            "map": ["map"]
        }
        
        for i, suggestion in enumerate(suggestions):
            for keyword, chart_types in keywords.items():
                if keyword in query_lower and suggestion["type"] in chart_types:
                    suggestion["score"] += 0.1
                    suggestion["description"] += f" (matched query term '{keyword}')"
        
        # Re-sort after adjusting scores
        suggestions = sorted(suggestions, key=lambda x: x["score"], reverse=True)
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def suggest_visualizations(self, df: pd.DataFrame, query: str) -> List[Dict[str, Any]]:
        """
        Suggest appropriate visualizations for a DataFrame.
        
        Args:
            df: The DataFrame to visualize
            query: The original query
            
        Returns:
            List of visualization suggestions
        """
        if df.empty:
            return []
        
        analysis = self._analyze_dataframe(df)
        suggestions = self._suggest_charts(analysis, query)
        
        return suggestions
    
    def _create_bar_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> str:
        """Create a bar chart and return as base64 image."""
        plt.figure(figsize=(10, 6))
        
        # Get data
        x = config.get("x_axis")
        y = config.get("y_axis")
        
        # Sort data if not too many categories
        if df[x].nunique() <= 20:
            df_plot = df.groupby(x)[y].sum().sort_values(ascending=False).reset_index()
        else:
            df_plot = df.groupby(x)[y].sum().reset_index().head(20)
        
        plt.bar(df_plot[x].astype(str), df_plot[y])
        plt.title(config.get("title", "Bar Chart"))
        plt.xlabel(x)
        plt.ylabel(y)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        
        # Convert plot to base64 string
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return img_str
    
    def _create_line_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> str:
        """Create a line chart and return as base64 image."""
        plt.figure(figsize=(10, 6))
        
        # Get data
        x = config.get("x_axis")
        y = config.get("y_axis")
        
        # Convert to datetime if needed
        if x in df.columns and not pd.api.types.is_datetime64_any_dtype(df[x]):
            try:
                df[x] = pd.to_datetime(df[x])
            except:
                pass
        
        # Group and sort by x
        df_plot = df.sort_values(by=x)
        
        plt.plot(df_plot[x], df_plot[y])
        plt.title(config.get("title", "Line Chart"))
        plt.xlabel(x)
        plt.ylabel(y)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Convert plot to base64 string
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return img_str
    
    def _create_pie_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> str:
        """Create a pie chart and return as base64 image."""
        plt.figure(figsize=(10, 6))
        
        # Get data
        values = config.get("values")
        labels = config.get("labels")
        
        # Group and calculate sums
        df_plot = df.groupby(labels)[values].sum()
        
        # If too many labels, keep only top ones
        if len(df_plot) > 8:
            other = df_plot.iloc[7:].sum()
            df_plot = df_plot.iloc[:7]
            df_plot.loc["Other"] = other
        
        plt.pie(df_plot, labels=df_plot.index, autopct='%1.1f%%')
        plt.title(config.get("title", "Pie Chart"))
        plt.axis('equal')
        
        # Convert plot to base64 string
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return img_str
    
    def _create_scatter_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> str:
        """Create a scatter chart and return as base64 image."""
        plt.figure(figsize=(10, 6))
        
        # Get data
        x = config.get("x_axis")
        y = config.get("y_axis")
        
        plt.scatter(df[x], df[y], alpha=0.7)
        plt.title(config.get("title", "Scatter Plot"))
        plt.xlabel(x)
        plt.ylabel(y)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Add trend line
        try:
            z = np.polyfit(df[x], df[y], 1)
            p = np.poly1d(z)
            plt.plot(df[x], p(df[x]), "r--", alpha=0.7)
        except:
            pass
        
        plt.tight_layout()
        
        # Convert plot to base64 string
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return img_str
    
    def _create_histogram(self, df: pd.DataFrame, config: Dict[str, Any]) -> str:
        """Create a histogram and return as base64 image."""
        plt.figure(figsize=(10, 6))
        
        # Get data
        values = config.get("values")
        
        plt.hist(df[values].dropna(), bins=20, alpha=0.7)
        plt.title(config.get("title", "Histogram"))
        plt.xlabel(values)
        plt.ylabel("Frequency")
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Convert plot to base64 string
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return img_str
    
    def generate_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a chart based on the configuration.
        
        Args:
            df: The DataFrame with the data
            config: Chart configuration
            
        Returns:
            Dictionary with chart data including base64 image
        """
        chart_type = config.get("type", "bar")
        result = {
            "type": chart_type,
            "title": config.get("title", "Chart"),
            "description": config.get("description", ""),
            "config": config
        }
        
        try:
            if chart_type == "bar":
                result["image"] = self._create_bar_chart(df, config)
            elif chart_type == "line":
                result["image"] = self._create_line_chart(df, config)
            elif chart_type == "pie":
                result["image"] = self._create_pie_chart(df, config)
            elif chart_type == "scatter":
                result["image"] = self._create_scatter_chart(df, config)
            elif chart_type == "histogram":
                result["image"] = self._create_histogram(df, config)
            else:
                result["error"] = f"Unsupported chart type: {chart_type}"
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def generate_all_suggested_charts(self, df: pd.DataFrame, query: str) -> List[Dict[str, Any]]:
        """
        Generate all suggested charts for a DataFrame.
        
        Args:
            df: The DataFrame to visualize
            query: The original query
            
        Returns:
            List of generated charts with base64 images
        """
        suggestions = self.suggest_visualizations(df, query)
        charts = []
        
        for config in suggestions:
            chart = self.generate_chart(df, config)
            charts.append(chart)
        
        return charts
    
    def get_chart_html(self, chart: Dict[str, Any]) -> str:
        """
        Generate HTML for displaying a chart.
        
        Args:
            chart: The chart data
            
        Returns:
            HTML string for the chart
        """
        if "error" in chart:
            return f"<div class='chart-error'>Error: {chart['error']}</div>"
        
        html = f"""
        <div class="chart-container">
            <h3>{chart['title']}</h3>
            <div class="chart-image">
                <img src="data:image/png;base64,{chart['image']}" alt="{chart['title']}">
            </div>
            <div class="chart-description">
                <p>{chart['description']}</p>
            </div>
        </div>
        """
        
        return html
    
    def get_all_charts_html(self, charts: List[Dict[str, Any]]) -> str:
        """
        Generate HTML for displaying multiple charts.
        
        Args:
            charts: List of chart data
            
        Returns:
            HTML string for all charts
        """
        if not charts:
            return "<div class='no-charts'>No charts available for this data</div>"
        
        html = "<div class='charts-container'>"
        
        for chart in charts:
            html += self.get_chart_html(chart)
        
        html += "</div>"
        
        # Add CSS
        html += """
        <style>
            .charts-container {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                justify-content: center;
            }
            .chart-container {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                margin: 10px 0;
                max-width: 600px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .chart-image img {
                max-width: 100%;
                height: auto;
            }
            .chart-description {
                color: #666;
                font-size: 14px;
                margin-top: 10px;
            }
            .chart-error {
                color: red;
                padding: 10px;
                border: 1px solid red;
                background: #fff8f8;
            }
        </style>
        """
        
        return html 
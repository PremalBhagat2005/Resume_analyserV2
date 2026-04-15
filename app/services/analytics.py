"""
Analytics module for Resume Analyser.
Provides data structuring with Pandas, numpy-based scoring, and visualization with Matplotlib.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for web environment
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, List, Tuple


class ResumeAnalytics:
    """Handle data analysis and visualization for resume analysis results."""
    
    def __init__(self, plots_dir: str = None):
        """
        Initialize analytics module.
        
        Args:
            plots_dir: Directory to save generated plots. Defaults to static/plots/
        """
        if plots_dir is None:
            plots_dir = os.path.join(
                os.path.dirname(__file__), '..', 'static', 'plots'
            )
        
        self.plots_dir = plots_dir
        self._ensure_plots_directory()
    
    def _ensure_plots_directory(self) -> None:
        """Ensure plots directory exists."""
        os.makedirs(self.plots_dir, exist_ok=True)
    
    def build_dataframe(self, ats_result: dict, match_result: dict = None,
                       extracted_entities: dict = None) -> pd.DataFrame:
        """
        Build a Pandas DataFrame from analysis results.
        
        Args:
            ats_result: Dictionary from calculate_ats_score()
            match_result: Dictionary from match_resume_to_job() (optional)
            extracted_entities: Extracted entities from NER (optional)
        
        Returns:
            pd.DataFrame: Structured results with all metrics
        """
        # Extract ATS scores
        breakdown = ats_result.get('breakdown', {})
        
        data = {
            'Metric': [
                'Overall ATS Score',
                'Contact Information',
                'Skills Section',
                'Education Section',
                'Experience Section',
                'Action Verbs & Keywords',
                'Resume Length',
            ],
            'Score': [
                ats_result.get('score', 0),
                breakdown.get('contact_info', 0),
                breakdown.get('skills_section', 0),
                breakdown.get('education_section', 0),
                breakdown.get('experience_section', 0),
                breakdown.get('action_verbs', 0),
                breakdown.get('resume_length', 0),
            ],
            'Max Points': [100, 20, 20, 15, 15, 20, 10]
        }
        
        df = pd.DataFrame(data)
        
        # Add match score if available
        if match_result:
            match_df = pd.DataFrame({
                'Metric': ['Job Match Score'],
                'Score': [match_result.get('match_score', 0)],
                'Max Points': [100]
            })
            df = pd.concat([df, match_df], ignore_index=True)
        
        # Add metadata
        df['Timestamp'] = datetime.now().isoformat()
        df['Word Count'] = ats_result.get('word_count', 0)
        df['Missing Sections'] = len(ats_result.get('missing_sections', []))
        df['Suggestions Count'] = len(ats_result.get('suggestions', []))
        
        if extracted_entities:
            df['Skills Found'] = len(extracted_entities.get('skills', []))
            df['Name Extracted'] = bool(extracted_entities.get('name'))
            df['Email Extracted'] = bool(extracted_entities.get('email'))
            df['Phone Extracted'] = bool(extracted_entities.get('phone'))
        
        return df
    
    def compute_numpy_scores(self, breakdown: dict) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Compute scores using NumPy arrays for better performance and analysis.
        
        Args:
            breakdown: Dictionary with section scores from calculate_ats_score()
        
        Returns:
            Tuple of (section_scores, max_points, mean_score)
        """
        # Define scoring structure
        sections = [
            'contact_info',
            'skills_section',
            'education_section',
            'experience_section',
            'action_verbs',
            'resume_length'
        ]
        
        max_points = np.array([20, 20, 15, 15, 20, 10], dtype=np.float32)
        
        # Extract scores for each section
        scores = np.array([
            breakdown.get(section, 0) for section in sections
        ], dtype=np.float32)
        
        # Compute mean score (for overall assessment)
        mean_score = float(np.mean(scores / max_points * 100))
        
        return scores, max_points, mean_score
    
    def generate_charts(self, ats_result: dict, match_result: dict = None,
                       extracted_entities: dict = None) -> Dict[str, str]:
        """
        Generate visualization charts and save as PNG files.
        
        Args:
            ats_result: Dictionary from calculate_ats_score()
            match_result: Dictionary from match_resume_to_job() (optional)
            extracted_entities: Extracted entities from NER (optional)
        
        Returns:
            Dict[str, str]: Paths to generated chart images
        """
        chart_paths = {}
        
        # Chart 1: ATS Score Breakdown Bar Chart
        try:
            chart_paths['ats_breakdown'] = self._generate_ats_breakdown_chart(
                ats_result['breakdown']
            )
        except Exception as e:
            print(f"Error generating ATS breakdown chart: {e}")
        
        # Chart 2: Skill Gap Comparison (if job description was provided)
        try:
            if match_result and extracted_entities:
                chart_paths['skill_comparison'] = self._generate_skill_comparison_chart(
                    match_result, extracted_entities
                )
        except Exception as e:
            print(f"Error generating skill comparison chart: {e}")
        
        # Chart 3: Score Trend (ATS + Match if available)
        try:
            chart_paths['score_summary'] = self._generate_score_summary_chart(
                ats_result, match_result
            )
        except Exception as e:
            print(f"Error generating score summary chart: {e}")
        
        return chart_paths
    
    def _generate_ats_breakdown_chart(self, breakdown: dict) -> str:
        """
        Generate ATS breakdown bar chart.
        
        Args:
            breakdown: Dictionary with section scores
        
        Returns:
            str: Relative path to saved chart
        """
        # Prepare data
        sections = [
            'Contact Info',
            'Skills',
            'Education',
            'Experience',
            'Action Verbs',
            'Resume Length'
        ]
        
        scores = [
            breakdown.get('contact_info', 0),
            breakdown.get('skills_section', 0),
            breakdown.get('education_section', 0),
            breakdown.get('experience_section', 0),
            breakdown.get('action_verbs', 0),
            breakdown.get('resume_length', 0)
        ]
        
        max_scores = [20, 20, 15, 15, 20, 10]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('#0a0a0f')
        ax.set_facecolor('#0a0a0f')
        
        # Create bars
        x = np.arange(len(sections))
        bars = ax.bar(x, scores, color='#00d4aa', edgecolor='#00d4aa', linewidth=1.5)
        
        # Styling
        ax.set_xlabel('ATS Sections', color='#ffffff', fontsize=11, fontweight='bold')
        ax.set_ylabel('Points Earned', color='#ffffff', fontsize=11, fontweight='bold')
        ax.set_title('ATS Score Breakdown', color='#ffffff', fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(sections, color='#ffffff', fontsize=9)
        ax.set_ylim(0, max(max_scores) + 5)
        
        # Color code bars based on performance
        for i, (bar, score, max_score) in enumerate(zip(bars, scores, max_scores)):
            if score >= max_score * 0.75:
                bar.set_color('#00d4aa')
            elif score >= max_score * 0.5:
                bar.set_color('#ffb800')
            else:
                bar.set_color('#ff4757')
        
        # Add value labels on bars
        for bar, score, max_score in zip(bars, scores, max_scores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(score)}/{int(max_score)}',
                   ha='center', va='bottom', color='#ffffff', fontsize=9, fontweight='bold')
        
        # Grid styling
        ax.grid(True, alpha=0.2, color='#00d4aa', linestyle='--', axis='y')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#00d4aa')
        ax.spines['bottom'].set_color('#00d4aa')
        
        # Set tick colors
        ax.tick_params(colors='#ffffff')
        
        plt.tight_layout()
        
        # Save chart
        filepath = os.path.join(self.plots_dir, 'ats_breakdown.png')
        plt.savefig(filepath, dpi=100, bbox_inches='tight', facecolor='#0a0a0f')
        plt.close()
        
        return f'/static/plots/ats_breakdown.png'
    
    def _generate_skill_comparison_chart(self, match_result: dict,
                                        extracted_entities: dict) -> str:
        """
        Generate skill gap comparison chart.
        
        Args:
            match_result: Dictionary from match_resume_to_job()
            extracted_entities: Extracted entities from NER
        
        Returns:
            str: Relative path to saved chart
        """
        # Prepare data
        matched_skills = match_result.get('matched_keywords', [])[:8]
        missing_skills = match_result.get('missing_keywords', [])[:8]
        
        categories = ['Matched Skills', 'Missing Skills']
        values = [len(matched_skills), len(missing_skills)]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#0a0a0f')
        ax.set_facecolor('#0a0a0f')
        
        # Create bars
        colors = ['#00d4aa', '#ff4757']
        bars = ax.bar(categories, values, color=colors, edgecolor=colors, linewidth=2, width=0.6)
        
        # Styling
        ax.set_ylabel('Number of Skills', color='#ffffff', fontsize=11, fontweight='bold')
        ax.set_title('Skill Gap Analysis', color='#ffffff', fontsize=14, fontweight='bold', pad=20)
        ax.set_ylim(0, max(values) + 3)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(value)}',
                   ha='center', va='bottom', color='#ffffff', fontsize=12, fontweight='bold')
        
        # Styling
        ax.tick_params(colors='#ffffff')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#ffffff')
        ax.spines['bottom'].set_color('#ffffff')
        
        plt.tight_layout()
        
        # Save chart
        filepath = os.path.join(self.plots_dir, 'skill_comparison.png')
        plt.savefig(filepath, dpi=100, bbox_inches='tight', facecolor='#0a0a0f')
        plt.close()
        
        return f'/static/plots/skill_comparison.png'
    
    def _generate_score_summary_chart(self, ats_result: dict,
                                     match_result: dict = None) -> str:
        """
        Generate overall score summary chart.
        
        Args:
            ats_result: Dictionary from calculate_ats_score()
            match_result: Dictionary from match_resume_to_job() (optional)
        
        Returns:
            str: Relative path to saved chart
        """
        # Prepare data
        ats_score = ats_result.get('score', 0)
        match_score = match_result.get('match_score', 0) if match_result else None
        
        if match_score is not None:
            scores = [ats_score, match_score]
            labels = ['ATS Score', 'Match Score']
        else:
            scores = [ats_score]
            labels = ['ATS Score']
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#0a0a0f')
        ax.set_facecolor('#0a0a0f')
        
        # Color based on score
        colors = []
        for score in scores:
            if score >= 75:
                colors.append('#00d4aa')
            elif score >= 50:
                colors.append('#ffb800')
            else:
                colors.append('#ff4757')
        
        # Create bars
        bars = ax.bar(labels, scores, color=colors, edgecolor=colors, linewidth=2, width=0.6)
        
        # Styling
        ax.set_ylabel('Score (0-100)', color='#ffffff', fontsize=11, fontweight='bold')
        ax.set_title('Resume Analysis Summary', color='#ffffff', fontsize=14, fontweight='bold', pad=20)
        ax.set_ylim(0, 110)
        
        # Add value labels on bars
        for bar, score in zip(bars, scores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(score)}/100',
                   ha='center', va='bottom', color='#ffffff', fontsize=12, fontweight='bold')
        
        # Add reference lines
        ax.axhline(y=75, color='#00d4aa', linestyle='--', alpha=0.3, linewidth=1)
        ax.axhline(y=50, color='#ffb800', linestyle='--', alpha=0.3, linewidth=1)
        
        # Styling
        ax.tick_params(colors='#ffffff')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#ffffff')
        ax.spines['bottom'].set_color('#ffffff')
        
        plt.tight_layout()
        
        # Save chart
        filepath = os.path.join(self.plots_dir, 'score_summary.png')
        plt.savefig(filepath, dpi=100, bbox_inches='tight', facecolor='#0a0a0f')
        plt.close()
        
        return f'/static/plots/score_summary.png'


# Convenience functions for easy integration
def create_analytics() -> ResumeAnalytics:
    """Factory function to create analytics instance."""
    return ResumeAnalytics()

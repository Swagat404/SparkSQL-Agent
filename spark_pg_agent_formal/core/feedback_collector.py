import os
import json
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd

class FeedbackCollector:
    """
    Collects and stores feedback for failed queries to improve the system.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize the feedback collector.
        
        Args:
            db_path: Path to the SQLite database for storing feedback
        """
        self.db_path = db_path or os.path.join(os.getcwd(), "spark_pg_agent_traces.db")
        self._initialize_db()
    
    def _initialize_db(self) -> None:
        """
        Initialize the SQLite database for storing feedback.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create feedback table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS query_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            generated_code TEXT,
            error_message TEXT,
            user_feedback TEXT,
            correct_code TEXT,
            db_type TEXT,
            timestamp TEXT,
            user_id TEXT,
            rating INTEGER
        )
        ''')
        
        # Create feedback tags table for categorizing feedback
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback_tags (
            feedback_id INTEGER,
            tag TEXT,
            PRIMARY KEY (feedback_id, tag),
            FOREIGN KEY (feedback_id) REFERENCES query_feedback (id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_feedback(
        self, 
        query: str, 
        generated_code: str = None, 
        error_message: str = None,
        user_feedback: str = None, 
        correct_code: str = None,
        db_type: str = "postgresql", 
        user_id: str = "anonymous",
        rating: int = None,
        tags: List[str] = None
    ) -> int:
        """
        Add feedback for a failed query.
        
        Args:
            query: The natural language query
            generated_code: The generated code that failed
            error_message: The error message from execution
            user_feedback: Additional feedback from the user
            correct_code: The corrected code provided by the user
            db_type: The database type ("postgresql" or "mysql")
            user_id: User identifier
            rating: User rating (1-5)
            tags: List of tags for categorizing the feedback
            
        Returns:
            The ID of the feedback entry
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        # Insert feedback
        cursor.execute('''
        INSERT INTO query_feedback (
            query, generated_code, error_message, user_feedback, 
            correct_code, db_type, timestamp, user_id, rating
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            query, generated_code, error_message, user_feedback,
            correct_code, db_type, timestamp, user_id, rating
        ))
        
        feedback_id = cursor.lastrowid
        
        # Insert tags if provided
        if tags:
            for tag in tags:
                cursor.execute('''
                INSERT INTO feedback_tags (feedback_id, tag) VALUES (?, ?)
                ''', (feedback_id, tag))
        
        conn.commit()
        conn.close()
        
        print(f"Feedback saved with ID: {feedback_id}")
        return feedback_id
    
    def get_feedback(self, feedback_id: int) -> Optional[Dict[str, Any]]:
        """
        Get feedback by ID.
        
        Args:
            feedback_id: The feedback ID
            
        Returns:
            Dictionary with feedback details or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get feedback
        cursor.execute('''
        SELECT * FROM query_feedback WHERE id = ?
        ''', (feedback_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        feedback = dict(row)
        
        # Get tags
        cursor.execute('''
        SELECT tag FROM feedback_tags WHERE feedback_id = ?
        ''', (feedback_id,))
        
        tags = [row["tag"] for row in cursor.fetchall()]
        feedback["tags"] = tags
        
        conn.close()
        return feedback
    
    def get_all_feedback(
        self, 
        limit: int = 100, 
        offset: int = 0, 
        tag: str = None,
        db_type: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get all feedback with optional filtering.
        
        Args:
            limit: Maximum number of entries to return
            offset: Offset for pagination
            tag: Filter by tag
            db_type: Filter by database type
            
        Returns:
            List of feedback entries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM query_feedback"
        params = []
        
        if tag:
            query = """
            SELECT qf.* FROM query_feedback qf
            JOIN feedback_tags ft ON qf.id = ft.feedback_id
            WHERE ft.tag = ?
            """
            params.append(tag)
        
        if db_type:
            if tag:
                query += " AND qf.db_type = ?"
            else:
                query += " WHERE db_type = ?"
            params.append(db_type)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute query
        cursor.execute(query, params)
        
        # Convert rows to dictionaries
        feedback_list = []
        for row in cursor.fetchall():
            feedback = dict(row)
            
            # Get tags for this feedback
            cursor.execute('''
            SELECT tag FROM feedback_tags WHERE feedback_id = ?
            ''', (feedback["id"],))
            
            tags = [row["tag"] for row in cursor.fetchall()]
            feedback["tags"] = tags
            
            feedback_list.append(feedback)
        
        conn.close()
        return feedback_list
    
    def get_error_analysis(self) -> Dict[str, Any]:
        """
        Analyze errors and feedback to identify patterns.
        
        Returns:
            Dictionary with error analysis results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        analysis = {
            "total_feedback": 0,
            "by_db_type": {},
            "common_tags": [],
            "rating_distribution": {},
            "recent_feedback": []
        }
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM query_feedback")
        analysis["total_feedback"] = cursor.fetchone()[0]
        
        # Get counts by database type
        cursor.execute("""
        SELECT db_type, COUNT(*) FROM query_feedback 
        GROUP BY db_type ORDER BY COUNT(*) DESC
        """)
        analysis["by_db_type"] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get common tags
        cursor.execute("""
        SELECT tag, COUNT(*) FROM feedback_tags 
        GROUP BY tag ORDER BY COUNT(*) DESC LIMIT 10
        """)
        analysis["common_tags"] = [{"tag": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        # Get rating distribution
        cursor.execute("""
        SELECT rating, COUNT(*) FROM query_feedback 
        WHERE rating IS NOT NULL GROUP BY rating ORDER BY rating
        """)
        analysis["rating_distribution"] = {str(row[0]): row[1] for row in cursor.fetchall()}
        
        # Get recent feedback (last 10)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, query, timestamp, error_message, rating FROM query_feedback 
        ORDER BY timestamp DESC LIMIT 10
        """)
        analysis["recent_feedback"] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return analysis
    
    def get_error_trends(self, days: int = 30) -> pd.DataFrame:
        """
        Get trends in errors over time.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            DataFrame with error trends
        """
        conn = sqlite3.connect(self.db_path)
        
        # Get data from the last N days
        query = f"""
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as count,
            db_type
        FROM 
            query_feedback
        WHERE 
            DATE(timestamp) >= DATE('now', '-{days} days')
        GROUP BY 
            DATE(timestamp), db_type
        ORDER BY 
            DATE(timestamp)
        """
        
        # Load into DataFrame
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def export_feedback(self, output_path: str) -> None:
        """
        Export all feedback to a JSON file.
        
        Args:
            output_path: Path to the output JSON file
        """
        feedback_list = self.get_all_feedback(limit=10000)
        
        with open(output_path, 'w') as f:
            json.dump(feedback_list, f, indent=2)
        
        print(f"Exported {len(feedback_list)} feedback entries to {output_path}")
    
    def import_feedback(self, input_path: str) -> int:
        """
        Import feedback from a JSON file.
        
        Args:
            input_path: Path to the input JSON file
            
        Returns:
            Number of imported entries
        """
        with open(input_path, 'r') as f:
            feedback_list = json.load(f)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        count = 0
        for feedback in feedback_list:
            # Extract tags
            tags = feedback.pop("tags", [])
            
            # Insert feedback
            cursor.execute('''
            INSERT INTO query_feedback (
                query, generated_code, error_message, user_feedback, 
                correct_code, db_type, timestamp, user_id, rating
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                feedback.get("query"), feedback.get("generated_code"),
                feedback.get("error_message"), feedback.get("user_feedback"),
                feedback.get("correct_code"), feedback.get("db_type"),
                feedback.get("timestamp"), feedback.get("user_id"),
                feedback.get("rating")
            ))
            
            feedback_id = cursor.lastrowid
            
            # Insert tags
            for tag in tags:
                cursor.execute('''
                INSERT INTO feedback_tags (feedback_id, tag) VALUES (?, ?)
                ''', (feedback_id, tag))
            
            count += 1
        
        conn.commit()
        conn.close()
        
        print(f"Imported {count} feedback entries from {input_path}")
        return count 
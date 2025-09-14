import sqlite3
import os
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd
import json

# Load environment variables
load_dotenv()

class NLToSQLEngine:
    def __init__(self, db_path='data/sample_business.db'):
        self.db_path = db_path
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.schema_info = self.get_database_schema()
        
    def get_database_schema(self):
        """Get database schema information for context"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        schema_info = {}
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            schema_info[table_name] = {}
            
            # Get column information
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            schema_info[table_name]['columns'] = []
            for col in columns:
                column_info = {
                    'name': col[1],
                    'type': col[2],
                    'not_null': bool(col[3]),
                    'primary_key': bool(col[5])
                }
                schema_info[table_name]['columns'].append(column_info)
            
            # Get foreign key information
            cursor.execute(f"PRAGMA foreign_key_list({table_name});")
            foreign_keys = cursor.fetchall()
            schema_info[table_name]['foreign_keys'] = foreign_keys
            
            # Get sample data (first 3 rows)
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            sample_data = cursor.fetchall()
            schema_info[table_name]['sample_data'] = sample_data
        
        conn.close()
        return schema_info
    
    def create_schema_context(self):
        """Create a readable schema description for the LLM"""
        context = "Database Schema:\n\n"
        
        for table_name, table_info in self.schema_info.items():
            context += f"Table: {table_name}\n"
            context += "Columns:\n"
            
            for col in table_info['columns']:
                pk_indicator = " (PRIMARY KEY)" if col['primary_key'] else ""
                not_null_indicator = " NOT NULL" if col['not_null'] else ""
                context += f"  - {col['name']} ({col['type']}){pk_indicator}{not_null_indicator}\n"
            
            # Add foreign key relationships
            if table_info['foreign_keys']:
                context += "Foreign Keys:\n"
                for fk in table_info['foreign_keys']:
                    context += f"  - {fk[3]} -> {fk[2]}.{fk[4]}\n"
            
            # Add sample data context
            if table_info['sample_data']:
                context += "Sample data (first few rows):\n"
                column_names = [col['name'] for col in table_info['columns']]
                context += f"  Columns: {', '.join(column_names)}\n"
                for row in table_info['sample_data'][:2]:  # Show only 2 sample rows
                    context += f"  Example: {row}\n"
            
            context += "\n"
        
        return context
    
    def generate_sql_query(self, natural_language_query):
        """Convert natural language to SQL using OpenAI"""
        
        schema_context = self.create_schema_context()
        
        prompt = f"""
You are an expert SQL assistant. Convert the natural language query into a valid SQLite query.

{schema_context}

Rules:
1. Only generate SELECT queries (no INSERT, UPDATE, DELETE)
2. Use proper SQL syntax for SQLite
3. Include appropriate JOINs when querying multiple tables
4. Use meaningful column aliases when needed
5. If the query is ambiguous, make reasonable assumptions
6. Return only the SQL query, no explanations

Natural Language Query: "{natural_language_query}"

SQL Query:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Clean up the response (remove markdown if present)
            if sql_query.startswith('```sql'):
                sql_query = sql_query[6:]
            if sql_query.endswith('```'):
                sql_query = sql_query[:-3]
            
            return sql_query.strip()
            
        except Exception as e:
            return f"Error generating SQL: {str(e)}"
    
    def execute_query(self, sql_query):
        """Execute SQL query and return results"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Use pandas for better formatting
            df = pd.read_sql_query(sql_query, conn)
            conn.close()
            
            return df, None
            
        except Exception as e:
            return None, str(e)
    
    def validate_sql_query(self, sql_query):
        """Basic validation to ensure query is safe"""
        # Convert to lowercase for checking
        query_lower = sql_query.lower().strip()
        
        # Check if it's a SELECT query
        if not query_lower.startswith('select'):
            return False, "Only SELECT queries are allowed"
        
        # Check for dangerous keywords
        dangerous_keywords = ['drop', 'delete', 'insert', 'update', 'alter']
        for keyword in dangerous_keywords:
            if keyword in query_lower:
                return False, f"Query contains forbidden keyword: {keyword}"
        
        return True, "Query is valid"
    
    def process_natural_language_query(self, user_query):
        """Main method to process user query"""
        print(f"\n{'='*50}")
        print(f"Processing: '{user_query}'")
        print(f"{'='*50}")
        
        # Step 1: Generate SQL
        print("🔄 Generating SQL query...")
        sql_query = self.generate_sql_query(user_query)
        
        if sql_query.startswith("Error"):
            return {
                'success': False,
                'error': sql_query,
                'user_query': user_query
            }
        
        print(f"📝 Generated SQL: {sql_query}")
        
        # Step 2: Validate SQL
        is_valid, validation_message = self.validate_sql_query(sql_query)
        if not is_valid:
            return {
                'success': False,
                'error': validation_message,
                'user_query': user_query,
                'sql_query': sql_query
            }
        
        # Step 3: Execute SQL
        print("⚡ Executing query...")
        results_df, error = self.execute_query(sql_query)
        
        if error:
            return {
                'success': False,
                'error': f"SQL execution error: {error}",
                'user_query': user_query,
                'sql_query': sql_query
            }
        
        # Step 4: Format results
        print("✅ Query executed successfully!")
        
        return {
            'success': True,
            'user_query': user_query,
            'sql_query': sql_query,
            'results': results_df,
            'row_count': len(results_df)
        }

def main():
    """Interactive command-line interface"""
    print("🚀 Natural Language to SQL Engine")
    print("Type 'quit' to exit, 'help' for examples")
    
    # Initialize engine
    try:
        engine = NLToSQLEngine()
        print("✅ Engine initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing engine: {e}")
        return
    
    # Interactive loop
    while True:
        try:
            user_input = input("\n🤖 Ask me anything about your database: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            elif user_input.lower() == 'help':
                print("\n📚 Example queries you can try:")
                print("- Show me all customers")
                print("- What are the total sales for each customer?")
                print("- Show me all electronics products")
                print("- Which customers are from California?")
                print("- What orders were placed in February 2024?")
                print("- Show me the most expensive products")
                print("- Which customer has spent the most money?")
                continue
            
            if not user_input:
                continue
            
            # Process the query
            result = engine.process_natural_language_query(user_input)
            
            if result['success']:
                print(f"\n📊 Results ({result['row_count']} rows):")
                print(result['results'].to_string(index=False))
            else:
                print(f"\n❌ Error: {result['error']}")
                if 'sql_query' in result:
                    print(f"Generated SQL: {result['sql_query']}")
                    
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
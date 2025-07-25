from pathlib import Path

def _get_query_from_file(file_path: str) -> str:
    """Helper function to read SQL file safely."""
    path = Path(__file__).parent / "SQL" / file_path  # Changed from "sql" to "SQL"
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError as e:
        print(f"Error: Could not find SQL file at {path}")
        raise e

query_params = {
    "count": _get_query_from_file("count_query.sql"),
    "data_lazada": _get_query_from_file("performance_query_lazada.sql"),
    "data_shopee": _get_query_from_file("performance_query_shopee.sql")
}

def get_query(query_name: str) -> str:
    """Gets a query by name from the pre-loaded dictionary."""
    query = query_params.get(query_name)
    if not query:
        raise ValueError(f"Query '{query_name}' not found. Available queries: {list(query_params.keys())}")
    return query
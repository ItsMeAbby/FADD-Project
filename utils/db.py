import pandas as pd
import duckdb
def save_to_duckdb( df: pd.DataFrame, table_name: str):
    """Saves a DataFrame to a DuckDB table."""
    df_copy = df.copy()
    # Clean column names to be SQL-friendly
    df_copy.columns = [str(col).replace(' ', '_').replace('(', '').replace(')', '').replace(',', '_') for col in df_copy.columns]
    # Continue as before

    con: duckdb.DuckDBPyConnection = create_connection()

    con.execute(f"DROP TABLE IF EXISTS {table_name}")
    con.register('temp_df', df_copy)
    con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM temp_df")
    con.unregister('temp_df')

    con.close()

def save_last_updated_time(league):
    """Saves the current date and time to DuckDB."""
    con = create_connection()
    con.execute("CREATE TABLE IF NOT EXISTS last_updated (last_updated TIMESTAMP, league VARCHAR(255))")
    con.execute("INSERT INTO last_updated VALUES (CURRENT_TIMESTAMP, ?)", [league])
    con.close()

def cal_time_passed(league):
    """Calculates the time passed since the last update. returns time passed in hours"""
    con = create_connection()
    con.execute("CREATE TABLE IF NOT EXISTS last_updated (last_updated TIMESTAMP, league VARCHAR(255))")
    result = con.execute("SELECT last_updated FROM last_updated WHERE league = ? ORDER BY last_updated DESC LIMIT 1", [league]).fetchdf()
    con.close()
    if result.empty:
        print("No last updated time found")
        return 1000
    else:
        # Get the last updated time
        last_updated = pd.to_datetime(result['last_updated'][0])
        current_time = pd.to_datetime('now')
        time_passed = (current_time - last_updated).seconds / 3600
        return time_passed

def create_connection():
    """Creates a connection to DuckDB."""
    con = duckdb.connect('soccer_data.db')
    return con

def load_from_duckdb(query: str):
    """Loads data from DuckDB."""
    con = create_connection()
    result = con.execute(query).fetchdf()
    con.close()
    return result


def load_data(league="PD", season="2024"):
    """Loads data from DuckDB."""

    
    standings_df = load_from_duckdb(f"SELECT * FROM standings WHERE season = '{season}' AND league = '{league}'")
    fixtures_df = load_from_duckdb(f"SELECT * FROM fixtures WHERE season = '{season}' AND league = '{league}'")
    form_df = load_from_duckdb(f"SELECT * FROM form WHERE season = '{season}' AND league = '{league}'")
    team_ratings_df = load_from_duckdb(f"SELECT * FROM team_ratings WHERE league = '{league}'")
    home_advantages_df = load_from_duckdb(f"SELECT * FROM home_advantages WHERE season = '{season}' AND league = '{league}'")
    upcoming_df = load_from_duckdb(f"SELECT * FROM upcoming WHERE league = '{league}'")

    fixtures_df['date'] = pd.to_datetime(fixtures_df['date'])
    upcoming_df['date'] = pd.to_datetime(upcoming_df['date'])
    form_df['date'] = pd.to_datetime(form_df['date'])
    
    return standings_df, fixtures_df, form_df, team_ratings_df, home_advantages_df, upcoming_df

if __name__ == "__main__":
    con=create_connection()
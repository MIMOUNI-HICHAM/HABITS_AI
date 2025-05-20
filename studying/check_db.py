import sqlite3

def check_database():
    conn = sqlite3.connect('studying.db')
    c = conn.cursor()
    
    # Check total records
    total = c.execute('SELECT COUNT(*) FROM study_sessions').fetchone()[0]
    print(f'Total records: {total}')
    
    # Get sample data
    print('\nSample data:')
    sample = c.execute('SELECT * FROM study_sessions LIMIT 5').fetchall()
    for row in sample:
        print(row)
    
    conn.close()

if __name__ == '__main__':
    check_database() 
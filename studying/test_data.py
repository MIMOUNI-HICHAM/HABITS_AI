from logic import get_study_data
import json

def test_data_retrieval():
    try:
        data = get_study_data()
        print("Data retrieved successfully!")
        print("\nSample of daily data:")
        print(json.dumps(data['dailyData'][:5], indent=2))
        print("\nWeekly comparison:")
        print(json.dumps(data['weeklyComparison'], indent=2))
        print("\nTopic balance:")
        print(json.dumps(data['topicBalance'], indent=2))
    except Exception as e:
        print(f"Error retrieving data: {str(e)}")

if __name__ == '__main__':
    test_data_retrieval() 
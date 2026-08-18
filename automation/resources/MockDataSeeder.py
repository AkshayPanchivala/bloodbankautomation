import requests

BASE_URL = "http://localhost:5000/api"

def seed_mock_data():
    print("Seeding mock data for tests...")
    
    # 1. Seed State
    state_payload = {"stateName": "MockState"}
    res = requests.post(f"{BASE_URL}/state", json=state_payload)
    print(f"State Seed: {res.status_code}")
    
    # 2. Seed City
    city_payload = {"stateName": "MockState", "cityName": "MockCity"}
    res = requests.post(f"{BASE_URL}/city/addcity", json=city_payload)
    print(f"City Seed: {res.status_code}")

    # 3. Seed User
    user_payload = {
        "firstName": "Mock",
        "lastName": "User",
        "gender": "Male",
        "dob": "1990-01-01",
        "age": 34,
        "phoneNo1": "9999999991",
        "phoneNo2": "9999999992",
        "email": "mockuser@example.com",
        "state": "MockState",
        "city": "MockCity",
        "address": "123 Mock St",
        "pinCode": 123456,
        "password": "Password123_",
        "passwordConfirm": "Password123_"
    }
    res = requests.post(f"{BASE_URL}/user/register", json=user_payload)
    print(f"User Seed: {res.status_code}")
    
    # 4. Login as Admin to get Token
    admin_login = requests.post(f"{BASE_URL}/admin/login", json={"email": "admin@example.com", "password": "Password123_"})
    admin_token = None
    if admin_login.status_code == 200:
        admin_token = admin_login.json().get('token')
        
    # 5. Seed Bloodbank
    if admin_token:
        headers = {"Authorization": f"Bearer {admin_token}"}
        bb_payload = {
            "state": "MockState",
            "city": "MockCity",
            "category": "Government",
            "bloodbankName": "Mock Bloodbank",
            "contactPerson": "Dr. Mock",
            "address1": "456 Blood Ave",
            "address2": "Suite B",
            "pinCode": 654321,
            "phoneNo1": "8888888881",
            "phoneNo2": "8888888882",
            "email": "mockbloodbank@example.com",
            "openingDate": "2023-01-01",
            "password": "Password123_",
            "passwordConfirm": "Password123_"
        }
        res = requests.post(f"{BASE_URL}/bloodbank/register", json=bb_payload, headers=headers)
        print(f"Bloodbank Seed: {res.status_code}")
    # 6. Seed Target User for RPA (Aditya)
    aditya_email = "adityamodi.imca22@gmail.com"
    aditya_payload = {
        "firstName": "Aditya",
        "lastName": "Modi",
        "gender": "Male",
        "dob": "1995-01-01",
        "age": 29,
        "phoneNo1": "7777777771",
        "phoneNo2": "7777777772",
        "email": aditya_email,
        "state": "MockState",
        "city": "MockCity",
        "address": "123 Test St",
        "pinCode": 123456,
        "password": "Password123_",
        "passwordConfirm": "Password123_"
    }
    res = requests.post(f"{BASE_URL}/user/register", json=aditya_payload)
    print(f"Aditya Seed: {res.status_code}")
    
    # 7. Seed Old Donation for Aditya (Using Pymongo)
    import pymongo
    from datetime import datetime, timedelta, timezone
    from bson.objectid import ObjectId
    
    MONGO_URI = "mongodb+srv://akshaypanchivala_db_user:akshaypanchivala_db_user@cluster0.klbtn0r.mongodb.net/blood_bank_management?retryWrites=true&w=majority&appName=Cluster0"
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client["blood_bank_management"]
        
        # Find aditya's user id
        user = db.users.find_one({"email": aditya_email})
            
        # Find mock bloodbank id
        bb = db.bloodbanks.find_one({"email": "mockbloodbank@example.com"})
        
        if user and bb:
            user_id = user["_id"]
            bb_id = bb["_id"]
            
            # Check if old donation already exists
            existing_donation = db.blooddonates.find_one({
                "userId": user_id, 
                "status": "Fulfilled"
            })
            
            if not existing_donation:
                # Insert a donation from exactly 90 days ago
                past_date = datetime.now(timezone.utc) - timedelta(days=90)
                db.blooddonates.insert_one({
                    "userId": user_id,
                    "bloodbankId": bb_id,
                    "bloodType": "A_Positive",
                    "status": "Fulfilled",
                    "whenToGive": past_date,
                    "message": "Seeded old donation",
                    "createdAt": past_date,
                    "updatedAt": past_date
                })
                print("Old Donation Seed: Successfully injected via PyMongo")
            else:
                print("Old Donation Seed: Already exists")
        else:
            print(f"Old Donation Seed: Failed to find User or Bloodbank in DB. User={user} BB={bb}")
    except Exception as e:
        print(f"Old Donation Seed Error: {e}")

if __name__ == "__main__":
    seed_mock_data()

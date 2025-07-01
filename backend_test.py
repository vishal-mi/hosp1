import requests
import json
import time
from datetime import datetime, timedelta
import sys

class HospitalBookingTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        result = "✅ PASS" if success else "❌ FAIL"
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        message = f"{result} - {name}"
        if details:
            message += f": {details}"
        
        print(message)
        self.test_results.append({"name": name, "success": success, "details": details})
        return success

    def run_request(self, method, endpoint, data=None, expected_status=200, auth=True):
        """Run a request and return the response"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            
            success = response.status_code == expected_status
            
            if success:
                try:
                    return success, response.json() if response.text else {}
                except json.JSONDecodeError:
                    return success, {}
            else:
                error_detail = response.json().get('detail', str(response.status_code)) if response.text else str(response.status_code)
                return False, {"error": error_detail, "status_code": response.status_code}
                
        except Exception as e:
            return False, {"error": str(e)}

    def test_create_sample_data(self):
        """Test creating sample data"""
        success, response = self.run_request('POST', 'create-sample-data', expected_status=200, auth=False)
        return self.log_test("Create Sample Data", success, response.get('message', str(response)))

    def test_register(self, email, name, phone, password, user_type="patient"):
        """Test user registration"""
        data = {
            "email": email,
            "name": name,
            "phone": phone,
            "password": password,
            "user_type": user_type
        }
        
        success, response = self.run_request('POST', 'register', data=data, expected_status=200, auth=False)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            return self.log_test("User Registration", True, f"Registered as {email}")
        else:
            return self.log_test("User Registration", False, str(response))

    def test_login(self, email, password):
        """Test user login"""
        data = {
            "email": email,
            "password": password
        }
        
        success, response = self.run_request('POST', 'login', data=data, expected_status=200, auth=False)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            return self.log_test("User Login", True, f"Logged in as {email}")
        else:
            return self.log_test("User Login", False, str(response))

    def test_analyze_symptoms(self, symptoms):
        """Test symptom analysis"""
        data = {
            "symptoms": symptoms,
            "patient_id": self.user_id
        }
        
        success, response = self.run_request('POST', 'analyze-symptoms', data=data, expected_status=200)
        
        if success and 'analysis' in response:
            details = f"Analysis received with {len(response.get('recommended_doctors', []))} doctor recommendations"
            return self.log_test("Symptom Analysis", True, details), response
        else:
            return self.log_test("Symptom Analysis", False, str(response)), None

    def test_get_doctors(self):
        """Test getting doctors list"""
        success, response = self.run_request('GET', 'doctors', expected_status=200, auth=False)
        
        if success and isinstance(response, list):
            return self.log_test("Get Doctors", True, f"Retrieved {len(response)} doctors"), response
        else:
            return self.log_test("Get Doctors", False, str(response)), None

    def test_book_appointment(self, doctor_id, symptoms):
        """Test booking an appointment"""
        # Schedule appointment for tomorrow
        appointment_date = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0).isoformat()
        
        data = {
            "doctor_id": doctor_id,
            "appointment_date": appointment_date,
            "symptoms": symptoms
        }
        
        success, response = self.run_request('POST', 'appointments', data=data, expected_status=200)
        
        if success and 'appointment_id' in response:
            return self.log_test("Book Appointment", True, f"Appointment booked with ID: {response['appointment_id']}"), response
        else:
            return self.log_test("Book Appointment", False, str(response)), None

    def test_get_appointments(self):
        """Test getting appointments"""
        success, response = self.run_request('GET', 'appointments', expected_status=200)
        
        if success and isinstance(response, list):
            return self.log_test("Get Appointments", True, f"Retrieved {len(response)} appointments"), response
        else:
            return self.log_test("Get Appointments", False, str(response)), None

    def test_update_appointment(self, appointment_id, status="cancelled"):
        """Test updating an appointment"""
        data = {
            "status": status
        }
        
        success, response = self.run_request('PUT', f'appointments/{appointment_id}', data=data, expected_status=200)
        
        if success and 'message' in response:
            return self.log_test("Update Appointment", True, response['message']), response
        else:
            return self.log_test("Update Appointment", False, str(response)), None

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n🏥 HOSPITAL BOOKING SYSTEM API TESTS 🏥\n")
        
        # Step 1: Create sample data
        self.test_create_sample_data()
        
        # Step 2: Test admin login
        admin_login = self.test_login("admin@hospital.com", "admin123")
        
        if not admin_login:
            print("\n❌ Admin login failed, cannot continue with admin tests")
        
        # Step 3: Register a new patient
        timestamp = int(time.time())
        email = f"patient{timestamp}@test.com"
        self.test_register(email, f"Test Patient {timestamp}", "1234567890", "password123")
        
        # Step 4: Get doctors
        doctors_success, doctors = self.test_get_doctors()
        
        # Step 5: Analyze symptoms
        symptoms = "I have been experiencing severe headaches and dizziness for the past 3 days. The pain is concentrated on the right side of my head and gets worse when I move suddenly."
        analysis_success, analysis = self.test_analyze_symptoms(symptoms)
        
        # Step 6: Book an appointment if doctors are available
        appointment_id = None
        if doctors_success and doctors and len(doctors) > 0:
            booking_success, booking = self.test_book_appointment(doctors[0]['id'], symptoms)
            if booking_success and booking:
                appointment_id = booking.get('appointment_id')
        
        # Step 7: Get appointments
        appointments_success, appointments = self.test_get_appointments()
        
        # Step 8: Update appointment if we have one
        if appointment_id:
            self.test_update_appointment(appointment_id)
        
        # Print summary
        print(f"\n📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    # Get the backend URL from frontend .env
    import os
    from dotenv import load_dotenv
    
    # Load the frontend .env file to get the backend URL
    load_dotenv("/app/frontend/.env")
    backend_url = os.environ.get("REACT_APP_BACKEND_URL")
    
    if not backend_url:
        print("❌ Error: REACT_APP_BACKEND_URL not found in frontend/.env")
        sys.exit(1)
    
    tester = HospitalBookingTester(backend_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)
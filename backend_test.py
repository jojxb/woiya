import requests
import sys
import json
from datetime import datetime, timedelta

class WOIYAMarketplaceAPITester:
    def __init__(self, base_url="https://woiya-connect.preview.emergentagent.com"):
        self.base_url = base_url
        self.seeker_token = None
        self.provider_token = None
        self.seeker_user = None
        self.provider_user = None
        self.test_job_id = None
        self.test_bid_id = None
        self.test_payment_id = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"   Response: {response.json()}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_user_registration(self):
        """Test user registration for both roles"""
        print("\n" + "="*50)
        print("TESTING USER REGISTRATION")
        print("="*50)
        
        # Register Service Seeker
        seeker_data = {
            "email": "seeker@test.com",
            "password": "test123",
            "full_name": "Test Seeker",
            "phone": "081234567890",
            "role": "pencari_jasa"
        }
        
        success, response = self.run_test(
            "Register Service Seeker",
            "POST",
            "api/auth/register",
            200,
            data=seeker_data
        )
        
        if success and 'token' in response:
            self.seeker_token = response['token']
            self.seeker_user = response['user']
            print(f"   Seeker ID: {self.seeker_user['id']}")
        
        # Register Service Provider
        provider_data = {
            "email": "provider@test.com",
            "password": "test123",
            "full_name": "Test Provider",
            "phone": "081234567891",
            "role": "penyedia_jasa"
        }
        
        success, response = self.run_test(
            "Register Service Provider",
            "POST",
            "api/auth/register",
            200,
            data=provider_data
        )
        
        if success and 'token' in response:
            self.provider_token = response['token']
            self.provider_user = response['user']
            print(f"   Provider ID: {self.provider_user['id']}")

    def test_user_login(self):
        """Test user login"""
        print("\n" + "="*50)
        print("TESTING USER LOGIN")
        print("="*50)
        
        # Test seeker login
        login_data = {
            "email": "seeker@test.com",
            "password": "test123"
        }
        
        success, response = self.run_test(
            "Login Service Seeker",
            "POST",
            "api/auth/login",
            200,
            data=login_data
        )
        
        # Test provider login
        login_data = {
            "email": "provider@test.com",
            "password": "test123"
        }
        
        success, response = self.run_test(
            "Login Service Provider",
            "POST",
            "api/auth/login",
            200,
            data=login_data
        )

    def test_user_profile(self):
        """Test getting user profile"""
        print("\n" + "="*50)
        print("TESTING USER PROFILE")
        print("="*50)
        
        if self.seeker_token:
            self.run_test(
                "Get Seeker Profile",
                "GET",
                "api/user/profile",
                200,
                token=self.seeker_token
            )
        
        if self.provider_token:
            self.run_test(
                "Get Provider Profile",
                "GET",
                "api/user/profile",
                200,
                token=self.provider_token
            )

    def test_job_creation(self):
        """Test job creation by service seeker"""
        print("\n" + "="*50)
        print("TESTING JOB CREATION")
        print("="*50)
        
        if not self.seeker_token:
            print("❌ No seeker token available for job creation")
            return
        
        job_data = {
            "title": "Perbaikan AC Rumah",
            "description": "Butuh teknisi untuk memperbaiki AC yang tidak dingin di rumah",
            "category": "perbaikan_rumah",
            "budget_min": 200000,
            "budget_max": 500000,
            "location": {"lat": -6.2088, "lng": 106.8456},
            "address": "Jl. Sudirman No. 123, Jakarta Pusat",
            "deadline": (datetime.now() + timedelta(days=7)).isoformat(),
            "requirements": ["Berpengalaman", "Membawa peralatan sendiri"]
        }
        
        success, response = self.run_test(
            "Create Job",
            "POST",
            "api/jobs",
            200,
            data=job_data,
            token=self.seeker_token
        )
        
        if success and 'job_id' in response:
            self.test_job_id = response['job_id']
            print(f"   Created Job ID: {self.test_job_id}")

    def test_job_listing(self):
        """Test job listing for both roles"""
        print("\n" + "="*50)
        print("TESTING JOB LISTING")
        print("="*50)
        
        # Test as seeker (should see own jobs)
        if self.seeker_token:
            self.run_test(
                "Get Jobs as Seeker",
                "GET",
                "api/jobs",
                200,
                token=self.seeker_token
            )
        
        # Test as provider (should see open jobs)
        if self.provider_token:
            success, response = self.run_test(
                "Get Jobs as Provider",
                "GET",
                "api/jobs",
                200,
                token=self.provider_token
            )
            
            if success and 'jobs' in response:
                print(f"   Found {len(response['jobs'])} available jobs")

    def test_job_details(self):
        """Test getting job details"""
        print("\n" + "="*50)
        print("TESTING JOB DETAILS")
        print("="*50)
        
        if not self.test_job_id:
            print("❌ No job ID available for testing")
            return
        
        if self.provider_token:
            self.run_test(
                "Get Job Details",
                "GET",
                f"api/jobs/{self.test_job_id}",
                200,
                token=self.provider_token
            )

    def test_bidding_system(self):
        """Test bidding system"""
        print("\n" + "="*50)
        print("TESTING BIDDING SYSTEM")
        print("="*50)
        
        if not self.test_job_id or not self.provider_token:
            print("❌ Missing job ID or provider token for bidding")
            return
        
        bid_data = {
            "job_id": self.test_job_id,
            "amount": 350000,
            "message": "Saya berpengalaman 5 tahun dalam perbaikan AC. Bisa selesai dalam 1 hari.",
            "completion_time": "1 hari"
        }
        
        success, response = self.run_test(
            "Place Bid",
            "POST",
            f"api/jobs/{self.test_job_id}/bids",
            200,
            data=bid_data,
            token=self.provider_token
        )
        
        if success and 'bid_id' in response:
            self.test_bid_id = response['bid_id']
            print(f"   Created Bid ID: {self.test_bid_id}")

    def test_bid_selection(self):
        """Test bid selection by job creator"""
        print("\n" + "="*50)
        print("TESTING BID SELECTION")
        print("="*50)
        
        if not self.test_job_id or not self.test_bid_id or not self.seeker_token:
            print("❌ Missing required data for bid selection")
            return
        
        self.run_test(
            "Select Bid",
            "POST",
            f"api/jobs/{self.test_job_id}/select-bid/{self.test_bid_id}",
            200,
            token=self.seeker_token
        )

    def test_payment_system(self):
        """Test payment creation and processing"""
        print("\n" + "="*50)
        print("TESTING PAYMENT SYSTEM")
        print("="*50)
        
        if not self.test_job_id or not self.test_bid_id or not self.seeker_token:
            print("❌ Missing required data for payment testing")
            return
        
        # Create payment
        payment_data = {
            "job_id": self.test_job_id,
            "bid_id": self.test_bid_id,
            "payment_method": "gopay",
            "amount": 350000
        }
        
        success, response = self.run_test(
            "Create Payment",
            "POST",
            "api/payments/create",
            200,
            data=payment_data,
            token=self.seeker_token
        )
        
        if success and 'payment_id' in response:
            self.test_payment_id = response['payment_id']
            print(f"   Created Payment ID: {self.test_payment_id}")
            print(f"   Gateway URL: {response.get('gateway_url', 'N/A')}")
        
        # Confirm payment (simulate payment gateway callback)
        if self.test_payment_id:
            self.run_test(
                "Confirm Payment",
                "POST",
                f"api/payments/{self.test_payment_id}/confirm",
                200
            )

    def test_wallet_functionality(self):
        """Test wallet and transaction history"""
        print("\n" + "="*50)
        print("TESTING WALLET FUNCTIONALITY")
        print("="*50)
        
        if self.seeker_token:
            success, response = self.run_test(
                "Get Seeker Wallet",
                "GET",
                "api/wallet",
                200,
                token=self.seeker_token
            )
            
            if success:
                print(f"   Seeker Balance: Rp {response.get('balance', 0):,}")
                print(f"   Recent Transactions: {len(response.get('recent_transactions', []))}")
        
        if self.provider_token:
            success, response = self.run_test(
                "Get Provider Wallet",
                "GET",
                "api/wallet",
                200,
                token=self.provider_token
            )
            
            if success:
                print(f"   Provider Balance: Rp {response.get('balance', 0):,}")
                print(f"   Recent Transactions: {len(response.get('recent_transactions', []))}")

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        print("\n" + "="*50)
        print("TESTING DASHBOARD STATISTICS")
        print("="*50)
        
        if self.seeker_token:
            success, response = self.run_test(
                "Get Seeker Dashboard Stats",
                "GET",
                "api/dashboard/stats",
                200,
                token=self.seeker_token
            )
            
            if success:
                print(f"   Total Jobs: {response.get('total_jobs', 0)}")
                print(f"   Active Jobs: {response.get('active_jobs', 0)}")
                print(f"   Completed Jobs: {response.get('completed_jobs', 0)}")
        
        if self.provider_token:
            success, response = self.run_test(
                "Get Provider Dashboard Stats",
                "GET",
                "api/dashboard/stats",
                200,
                token=self.provider_token
            )
            
            if success:
                print(f"   Total Bids: {response.get('total_bids', 0)}")
                print(f"   Selected Bids: {response.get('selected_bids', 0)}")
                print(f"   Total Earnings: Rp {response.get('total_earnings', 0):,}")

    def test_messaging_system(self):
        """Test messaging between users"""
        print("\n" + "="*50)
        print("TESTING MESSAGING SYSTEM")
        print("="*50)
        
        if not self.seeker_user or not self.provider_user or not self.seeker_token or not self.provider_token:
            print("❌ Missing user data for messaging test")
            return
        
        # Send message from seeker to provider
        message_data = {
            "recipient_id": self.provider_user['id'],
            "content": "Halo, kapan bisa mulai perbaikan AC?",
            "job_id": self.test_job_id
        }
        
        success, response = self.run_test(
            "Send Message (Seeker to Provider)",
            "POST",
            "api/messages",
            200,
            data=message_data,
            token=self.seeker_token
        )
        
        # Get conversation
        if success:
            self.run_test(
                "Get Conversation",
                "GET",
                f"api/messages/{self.provider_user['id']}",
                200,
                token=self.seeker_token
            )

    def test_rating_system(self):
        """Test rating system"""
        print("\n" + "="*50)
        print("TESTING RATING SYSTEM")
        print("="*50)
        
        if not self.test_job_id or not self.provider_user or not self.seeker_token:
            print("❌ Missing required data for rating test")
            return
        
        rating_data = {
            "target_user_id": self.provider_user['id'],
            "job_id": self.test_job_id,
            "rating": 5,
            "comment": "Pekerjaan sangat memuaskan, cepat dan profesional!"
        }
        
        self.run_test(
            "Submit Rating",
            "POST",
            "api/ratings",
            200,
            data=rating_data,
            token=self.seeker_token
        )

    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🚀 Starting WOIYA Marketplace API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        
        try:
            # Core authentication tests
            self.test_user_registration()
            self.test_user_login()
            self.test_user_profile()
            
            # Job management tests
            self.test_job_creation()
            self.test_job_listing()
            self.test_job_details()
            
            # Bidding workflow tests
            self.test_bidding_system()
            self.test_bid_selection()
            
            # Payment system tests
            self.test_payment_system()
            
            # Additional features
            self.test_wallet_functionality()
            self.test_dashboard_stats()
            self.test_messaging_system()
            self.test_rating_system()
            
        except Exception as e:
            print(f"\n❌ Test suite failed with error: {str(e)}")
        
        # Print final results
        print("\n" + "="*60)
        print("FINAL TEST RESULTS")
        print("="*60)
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All tests passed! API is working correctly.")
            return 0
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} test(s) failed. Please check the issues above.")
            return 1

def main():
    tester = WOIYAMarketplaceAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
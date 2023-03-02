from django.conf import settings
from django.conf.urls import url
import requests
import json

class Paystack:
    PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
    base_url = "https://api.paystack.co"
    bank_url = "https://api.paystack.co/bank"
    charge_url = "https://api.paystack.co/charge"
    otp_url = "https://api.paystack.co/charge/submit_otp"
    transfers_url = "https://api.paystack.co/transfer/bulk"
    recipient_url = "https://api.paystack.co/transferrecipient"
    

    headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
#                       charge customer
#                       create recipient
#                       otp to complete charge
#                       get banks and thier code 
#                       tranfer to the recipient
#                       manually check if charge went through
#                       manually check if transfer went through

    def charge(self,email,amount,bank_code,account_number,is_kuda,phone,token,birthday):
        url = self.charge_url
        if is_kuda == True:
            bank_details = {
                "code":  f"{bank_code}",  
                "phone": f"{phone}", 
                "token": f"{token}", 
            }
        else:
            bank_details = {
                "code": f"{bank_code}", 
                "account_number":f"{account_number}",
            }

        data1 = {
            "email": f"{email}",  
            "amount": amount, 
            "bank": bank_details,
            "birthday": f"{birthday}"
        }
        data2 = json.dumps(data1 , indent=4)
        response = requests.post(url=url , headers=self.headers , data=data2)
        response_data = response.json()
        
        if response.status_code == 200:
            data =response_data['data']
            status = data['status']
            ref = data['reference']
            message = data['display_text']
        else:
            status = False
            ref = None
            message = response_data['message']
        return status,ref,message

    def create_recipient(self,name,bank,account_number):
        url = self.recipient_url
        
        data1 = {
            "type": f"{bank.type}",
            "name": f"{name}",
            "account_number": f"{account_number}",
            "bank_code": f"{bank.bank_code}",
            "currency": f"{bank.currency}"
        }
        data2 = json.dumps(data1 , indent=4)
        response = requests.post(url=url , headers=self.headers , data=data2)
        response_data = response.json()
        if response.status_code == 201:
            data = response_data['data']
            recipient = data['recipient_code']
        else:
            recipient = None
        return recipient

    def otp(self,otp,ref):
        url = self.otp_url
        
        data1 = { "otp": f"{otp}", "reference": f"{ref}" }
        data2 = json.dumps(data1 , indent=3)
        response = requests.post(url=url , headers=self.headers , data=data2)
        response_data = response.json()
        if response.status_code == 200:
            data =response_data['data']
            status = data['status']
            if status =='success':
                message = "success"
            elif status =='send_otp':
                message = data['display_text']
            elif status =='pending':
                message = "pending"
            elif status =='send_pin':
                message = data['display_text']
            elif status =='failed':
                message = "failed"
            elif status =='open_url':
                message = data['url']
            elif status =='send_phone':
                message = data['display_text']
            elif status =='send_birthday':
                message = data['display_text']

        else:
            status = response_data['status']
            message = response_data['message']
        return status,message

    def get_banks(self , *args , **kwargs):
        # "code": "058", 
        # "account_number":"0498708865"
        # "code": "033", 
        # "account_number":"2133934830"
        url= self.bank_url
        response = requests.get(url=url , headers=self.headers)
        if response.status_code == 200:
            response_data = response.json()
            return response_data

    def transfer(self,tranferlist):
        url = self.transfers_url
        
        data1 = { 
            "currency": "NGN",
            "source": "balance", 
            "transfers": tranferlist
        }
        data2 = json.dumps(data1 , indent=5)
        response = requests.post(url=url , headers=self.headers , data=data2)
        response_data = response.json()
        status = response_data['status']
        if response.status_code == 200:
            data =response_data['data']
        else:
            data = response_data['message']
        return status,data

    def manually_verify_charge(self , ref , *args , **kwargs):
        path = f"/charge/{ref}"
        url= self.base_url + path
        response = requests.get(url=url , headers=self.headers)
        response_data = response.json()
        if response.status_code == 200:
            data =response_data['data']
            status = data['status']
            if status =='success':
                message = "success"
            elif status =='send_otp':
                message = data['display_text']
            elif status =='pending':
                message = "pending"
            elif status =='send_pin':
                message = data['display_text']
            elif status =='failed':
                message = "failed"
            elif status =='open_url':
                message = data['url']
            elif status =='send_phone':
                message = data['display_text']
            elif status =='send_birthday':
                message = data['display_text']
            return status,message

    def manually_verify_transfer(self , ref , *args , **kwargs):
        path = f"/transfer/verify/{ref}"
        url= self.base_url + path
        response = requests.get(url=url , headers=self.headers)
        if response.status_code == 200:
            response_data = response.json()
            status = response_data['status']
            return status
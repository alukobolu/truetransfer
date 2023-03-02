import secrets
from dateutil.relativedelta import SA
from django.http.response import HttpResponse
from django.http.request import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from .models import Bank,Recipients,Charges,Transfer
import time


paginator = PageNumberPagination()
paginator.page_size = 20

def transfer(charge):
    trans = Transfer.objects.create(
                        recipient = charge.recipient,
                        associated_charge = charge
                    )
    trans.save()
    list = []
    data = {}
    data['amount'] = trans.associated_charge.amount_value()
    data['recipient'] = trans.recipient.recipient_code
    data['reference'] = trans.ref
    list.append(data)
    status,result =trans.make_transfer(list)
    if status == True:
        for f in result:
            trans.transfer_code  = f['transfer_code']
            status1 = trans.verify_transfer(trans.ref)
            if status1 == True:
                trans.verified == True
            trans.save()

class Charge(APIView):

    def post(self,request):
        email = request.POST['email']
        amount = request.POST['amount']
        bankid = request.POST['bankid']
        recipientid = request.POST['recipientid']
        birthday = request.POST['birthday']

        bank = Bank.objects.get(bank_id=bankid)
        recipient = Recipients.objects.get(recipient_id=recipientid)

        if bank.name =='kuda':
            phone = request.POST['phone']
            token = request.POST['token']
            charge = Charges.objects.create(
                email = email,
                phone = phone,
                token = token,
                amount = amount,
                bank = bank,
                recipient = recipient,
                birthday = birthday
            )
        else:
            account_number = request.POST['account_number']
            charge = Charges.objects.create(
                email = email,
                account_number = account_number,
                amount = amount,
                bank = bank,
                recipient = recipient,
                birthday = birthday
            )
        charge.set_check_code()
        result =charge.charging()
        data ={}
        if result != False:
            data["Success"] = "Enter otp"
            data["Reference"] = charge.ref
        else:
            data["Error"] = "Sorry something went wrong"
        return Response(data=data)

    def get(self,request):
        user = request.user
        recipient = Recipients.objects.get(user=user)
        charge_list = Charges.objects.filter(recipient=recipient)
        context = []
        for f in charge_list:
            data ={} 
            data["email"]  = str(f.email)
            data["amount"]   = str(f.amount)
            data["status"]   = str(f.status)
            data["seen"]   = f.seen
            data["verified"]   = f.verified
            data["date_created"]   = f.date_created 
            context.append(data)
        context = paginator.paginate_queryset(context, request)
        return paginator.get_paginated_response(context)

class Submit_otp(APIView):
    def post(self,request):
        otp = request.POST['otp']
        ref = request.POST['ref']
        charge = Charges.objects.get(ref=ref)
        status,message = charge.send_otp(otp)
        if status == 'success':
            charge.status = status
            x = 0
            while x != -1:
                time.sleep(x)
                status1,message1=charge.manually_verify()
                if status1 == 'success':
                    charge.verified = True
                    charge.save()
                    transfer(charge)
                    x = -1
                elif status1 == 'pending':
                    x = x + 5
                else:
                    x = -1
                    data = {}
                    data["Status"] = status1
                    data["Message"] = message1
                    return Response(data=data)
        data = {}
        data["Status"] = status
        data["Message"] = message
        return Response(data=data)

class Cross_check_charge(APIView):
    def post(self,request):
        check_code = request.POST['check_code']
        ref = request.POST['ref']

        charge = Charges.objects.get(check_code=check_code,ref=ref)
        charge.seen = True
        data ={}
        data["Success"] = True
        return Response(data=data)
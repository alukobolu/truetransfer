from django.db import models
import secrets

from requests.models import requote_uri
from .paystack import Paystack
import datetime
from dateutil.relativedelta import relativedelta
import uuid #For unique characters
# Create your models here.

class Bank(models.Model):
    name =  models.CharField(max_length=200)
    bank_id =  models.UUIDField(default=uuid.uuid4, editable=False,unique=True, null=True)
    pay_with_bank  = models.BooleanField(null=True)
    bank_code = models.PositiveIntegerField()
    slug = models.CharField(max_length=200,null=True)
    type = models.CharField(max_length=200,default="nuban")
    country = models.CharField(max_length=200,null=True)
    currency = models.CharField(max_length=200,default="NGN")
    date_created =models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_created',)

    def __str__(self) -> str:
        return f'{self.name}'

    def get_banklist(self):
        paystack = Paystack()
        result = paystack.get_banks()
        return result

class Recipients (models.Model):
    recipient_id =  models.UUIDField(default=uuid.uuid4, editable=False,unique=True, null=True)
    user =      models.ForeignKey(to='accounts.Account',on_delete=models.CASCADE,null=True)
    name         =        models.CharField(max_length=200,null=True)
    recipient_code    =   models.CharField(max_length=200,null=True)  
    account_name =  models.CharField(max_length=200,null=True)
    account_number     =  models.CharField(max_length=200,null=True)
    bank       =          models.ForeignKey(Bank,on_delete=models.CASCADE,null=True)
    date_created =models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_created',)

    def __str__(self) -> str:
        return f'{self.name}'

    def creating_recipient(self,*args,**kwargs):
        paystack = Paystack()
        recipient = paystack.create_recipient(self.name,self.bank,self.account_number)
        if recipient != None:
            self.recipient_code = recipient
            super().save(*args,**kwargs)
            return True
        return False

class Charges(models.Model):
    charge_id =  models.UUIDField(default=uuid.uuid4, editable=False,unique=True, null=True)
    email = models.EmailField(unique=False,null=True)
    account_number= models.CharField(max_length=200,null=True)
    amount =        models.CharField(max_length=200,null=True)
    bank =          models.ForeignKey(Bank,on_delete=models.CASCADE,null=True)  
    recipient =      models.ForeignKey(Recipients,on_delete=models.CASCADE,null=True)
    phone  =        models.CharField(max_length=200,null=True)
    token =         models.CharField(max_length=200,null=True)
    birthday =      models.CharField(max_length=200,null=True)

    status =        models.CharField(max_length=200,null=True)
    ref    =        models.CharField(max_length=200,null=True)
    verified =      models.BooleanField(default=False)

    check_code =  models.CharField(max_length=200,null=True)
    seen =      models.BooleanField(default=False)  
    date_created =  models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_created',)

    def __str__(self) -> str:
        return f'{self.email}'

    def amount_value(self) -> int:
        return self.amount*100

    def set_check_code(self,*args,**kwargs) -> None:
        while not self.check_code:
            check_code = secrets.token_urlsafe(50)
            object_with_similar_check_code = Charges.objects.filter(check_code=check_code)
            if not object_with_similar_check_code:
                self.check_code = check_code
        super().save(*args,**kwargs)

    def charging(self,*args,**kwargs):
        paystack = Paystack()
        is_kuda = False
        amount = self.amount_value()
        if self.bank.name == 'Kuda':
            is_kuda = True
        status,ref,message = paystack.charge(self.email , amount, self.bank.back_code , self.account_number, is_kuda,self.phone, self.token,self.birthday)
        if status != False:
            self.ref = ref
            self.status = status
        super().save(*args,**kwargs)
        return status

    def send_otp(self,otp):
        paystack = Paystack()
        status,message = paystack.otp(otp,self.ref)
        return status,message

    def manually_verify(self):
        paystack = Paystack()
        status,message = paystack.manually_verify_charge(self.ref)
        return status,message

class Transfer(models.Model):
    transfer_id =  models.UUIDField(default=uuid.uuid4, editable=False,unique=True, null=True)
    recipient =      models.ForeignKey(Recipients,on_delete=models.CASCADE,null=True)
    associated_charge =      models.OneToOneField(Charges,on_delete=models.CASCADE,null=True)

    status =        models.CharField(max_length=200,null=True)
    ref    =        models.CharField(max_length=200,null=True)
    transfer_code    =        models.CharField(max_length=200,null=True)
    verified =      models.BooleanField(default=False)

    date_created =  models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_created',)

    def __str__(self) -> str:
        return f'{self.recipient.name}'

    def save(self,*args,**kwargs) -> None:
        while not self.ref:
            ref = secrets.token_urlsafe(50)
            object_with_similar_ref = Transfer.objects.filter(ref=ref)
            if not object_with_similar_ref:
                self.ref = ref
        super().save(*args,**kwargs)

    def make_transfer(self,list):
        paystack = Paystack()
        status,result = paystack.transfer(list)
        return status,result

    def verify_transfer(self,ref):
        paystack = Paystack()
        status = paystack.manually_verify_transfer(ref)
        return status

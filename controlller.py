from model import *
from main import db, api, FERNET_KEY
from flask_restful import Api, Resource
from flask import Flask, jsonify, request, Response
from sqlalchemy import and_
import random, string, bcrypt
from functools import wraps
from datetime import datetime,date,timedelta
import json


class User(db.Model):
    __tablename__="users"
    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    name=db.Column("name", db.String(50), default=None)
    phone=db.Column("phone",db.String(15),default=None)
    email=db.Column("email",db.String(50),default=None)
    password=db.Column("password",db.String(500),default=None)
    is_delete=db.Column("is_delete",db.Boolean,default=0)
    wallet=db.Column("wallet",db.Integer,default=0)
    
class Session(db.Model):
    __tablename__="session"
    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    token=db.Column(db.String,primary_key=True)
    user_id=db.Column(db.String,primary_key=True)
    is_delete=db.Column("is_delete",db.Boolean,default=0)
    user = db.relationship('User', foreign_keys=user_id,
                           primaryjoin="Session.user_id==User.id")

class AllProducts(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    price = db.Column(db.Float(precision=2))
    description=db.Column(db.String(80))
    qty=user_id = db.Column(db.Integer)
    image = db.Column(db.String(80))
    product_type = db.Column(db.String(80))
    is_added = db.column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User')

    @classmethod
    def find_by_name(cls, name):
        return cls.query.filter_by(name=name).first()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

class Cart(db.Model):
    __tablename__ = 'cart'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    price = db.Column(db.Float(precision=2))
    description=db.Column(db.String(80))
    product_type = db.Column(db.String(80))
    qty = db.Column(db.Integer)
    image = db.Column(db.String(80))
    is_added = db.column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    #product = db.relationship('AllProducts')


class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer,  primary_key=True)
    none= db.Column(db.String(80))


class Bill(db.Model):
    __tablename__ = 'billgenerate'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(80))
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    description=db.Column(db.String(80))
    total_price = db.Column(db.Integer)
    date_time = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    #cart = db.relationship('Cart')

def get_hashed_password(plain_text_password):
    # Hash a password for the first time
    #   (Using bcrypt, the salt is saved into the hash itself)
    plain_text_password = bytes(plain_text_password, 'utf-8')
    return bcrypt.hashpw(plain_text_password, bcrypt.gensalt())

def check_password(plain_text_password, hashed_password):
    # Check hashed password. Using bcrypt, the salt is saved into the hash itself
    plain_text_password = bytes(plain_text_password, 'utf-8')
    hashed_password = bytes(hashed_password, 'utf-8')
    return bcrypt.checkpw(plain_text_password, hashed_password)

def errorMessage(text):
    result={
        "error": text,
        "status": False
    }
    response=jsonify(result)
    response.status_code=200
    return response

def authenticate_api(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            authtoken = request.headers['authtoken']
        except:
            return Response('Authentication Error! Auth Token is missing', 401, {'WWW-Authenticate': 'API token error'})
        authObj = Session.query.filter(and_(Session.token == authtoken, Session.is_delete == 0)).first()
        # print(authObj)
        if not authObj:
            return Response('Authentication Error! Token is invalid or does not belong to the user', 401,
                            {'WWW-Authenticate': 'API token error'})
        kwargs['session'] = authObj
        kwargs['user'] = authObj.user
        return f(*args, **kwargs)

    return wrapper
class hello(Resource):
    def get(self):
        result = {"msg": "how"}
        return jsonify(result)

class Signup(Resource):
    def post(self):
        data=request.get_json()
        if "phone" in data.keys():
            phone=data["phone"]
            phone = "+91"+str(phone)
        else:
            return errorMessage("phone number is required")

        if "password" in data.keys():
            password=data["password"]
        else:
            return errorMessage("password is required")
        if "name" in data.keys():
            name=data["name"]
        else:
            return errorMessage("name is required")
        if "email" in data.keys():
            email=data["email"]
        else:
            return errorMessage("email is required")
        get_user_by_email = User.query.filter(and_(User.email == email, User.is_delete == 0)).first()
        get_user_by_phone = User.query.filter(and_(User.phone == phone, User.is_delete == 0)).first()
        if get_user_by_phone is not None or get_user_by_email is not None:
            return errorMessage("Your credentials already exists")
        en_pass = get_hashed_password(password)
        new_user=User(phone=phone,password=en_pass,name=name, email=email)
        db.session.add(new_user)
        db.session.commit()
        token=''.join(random.choices(
            string.ascii_uppercase+string.digits,k=50))
        new_session=Session(user_id=new_user.id,token=token)
        print(new_user.password)
        db.session.add(new_session)
        db.session.commit()
        result={
            "error":"",
            "status":True,
            "Token":token
        }
        response=jsonify(result)
        response.status_code=200
        return response

class LoginWithPassword(Resource):
    def post(self):
        data = request.get_json()
        if "user_details" in data.keys():
            user_details = data["user_details"]
        else:
            return errorMessage("user_details is required")
        if "password" in data.keys():
            password = data["password"]
        else:
            return errorMessage("password is required")
        token=''.join(random.choices(
            string.ascii_uppercase+string.digits,k=50))
        search_user = User.query.filter(and_(User.email == user_details, User.is_delete == 0)).first()
        if search_user is None:
            search_user = User.query.filter(and_(User.phone == "+91"+ str(user_details), User.is_delete == 0)).first()
        if search_user is None:
            return errorMessage("User does not exists")
        password_decode = ""
        if search_user.password is not None:
            password_decode = check_password(password, search_user.password)
        if password_decode == True:
            new_session = Session(user_id = search_user.id, token=token)
            db.session.add(new_session)
            db.session.commit()
        else:
            return errorMessage("Wrong Password")
        result = {
            "error": "",
            "status": True,
            "name": search_user.name,
            "phone": search_user.phone,
            "email": search_user.email,
            "token": token
        }
        return jsonify(result)

class Logout(Resource):
    @authenticate_api
    def get(self, **kwargs):
        session = kwargs['session']
        get_session = Session.query.filter(and_(Session.id == session.id, Session.is_delete == 0)).first()
        print(get_session)
        db.session.delete(get_session)
        db.session.commit()
        result = {
            "error": "",
            "status": True
        }
        return jsonify(result)

class LoginWithAccount(Resource):
    def post(self):
        data = request.get_json()
        if "email" in data.keys():
            email = data["email"]
        else:
            return errorMessage("email is required")
        if "name" in data.keys():
            name = data["name"]
        else:
            name= None
        token=''.join(random.choices(
            string.ascii_uppercase+string.digits,k=50))
        get_user = User.query.filter(and_(User.email == email, User.is_delete == 0)).first()
        if get_user is not None:
            new_session = Session(token=token, user_id=get_user.id)
            db.session.add(new_session)
            db.session.commit()
            result = {
                "error": "",
                "status": True,
                "name": get_user.name,
                "phone": get_user.phone,
                "email": get_user.email,
                "token": token
            }
            return jsonify(result)
        else:
            add_user = User(email=email, name=name)
            db.session.add(add_user)
            db.session.commit()
            new_session = Session(user_id = add_user.id, token=token)
            db.session.add(new_session)
            db.session.commit()
            result = {
                "error": "",
                "status": True,
                "name": add_user.name,
                "email": add_user.email,
                "token": token
            }
            return jsonify(result)

class ProfileInfo(Resource):
    @authenticate_api
    def get(self, **kwargs):
        user = kwargs["user"]
        result = {
            "id": user.id,
            "name": user.name,
            "phone": user.phone,
            "email": user.email
        }
        return jsonify(result)

class UpdateProfile(Resource):
    @authenticate_api
    def post(self, **kwargs):
        user = kwargs["user"]
        data = request.get_json()
        if "user_name" in data.keys():
            name = data["user_name"]
        else:
            name = None
        if name is not None:
            user.name = name
            db.session.add(user)
            db.session.commit()
        result = {
            "error": "",
            "status": True
        }
        return jsonify(result)

#Enables seller to add his own products
class AddAllProducts(Resource):
    @authenticate_api
    def post(self,**kwargs):
        User = kwargs["user"]
        data=request.get_json()
        name=data["name"]
        price=data["price"]
        product_type=data["product_type"]
        user_id=User.id
        description=data["description"]
        qty=data["qty"]
        image=data["image"]
        get_user = AllProducts.query.filter(and_(AllProducts.name==name,AllProducts.qty==qty,user_id==AllProducts.user_id)).first()
        if get_user is not None:
            return errorMessage("Product already exists")
        entry=AllProducts(name=name,price=price,description=description, is_added=0, product_type=product_type, user_id=User.id, qty=qty,image=image)
        db.session.add(entry)
        db.session.commit()
        result = {
            "error": "",
            "status": True
        }
        return jsonify(result) 

#Displays all products of the seller
class DisplayAllProducts(Resource):
    @authenticate_api
    def get(self,**kwargs):
        User = kwargs["user"]
        get_allproducts=AllProducts.query.filter((User.id==AllProducts.user_id)).all()
        result=[]
        for product in get_allproducts:
            result.append ({
            "name": product.name,
            "price": product.price,
            "description": product.description,
            "type": product.product_type,
            "qty": product.qty,
            "image": product.image
        })
        
        return jsonify(result)
        #return result1

#Displays all the added items in the cart
class DisplayCart(Resource):
    @authenticate_api
    def get(self,**kwargs):
        User = kwargs["user"]
        get_allproducts=Cart.query.filter(and_(User.id==Cart.user_id)).all()
        result=[]
        for product in get_allproducts:
            result.append ({
            "name": product.name,
            "price": product.price,
            "description": product.description,
            "type": product.product_type,
            "qty": product.qty,
             "image": product.image
        })
        return jsonify(result)

#Adds product or products to cart
class AddtoCart(Resource):
    @authenticate_api
    def post(self,**kwargs):
        User = kwargs["user"]
        data=request.get_json()
        get_product=AllProducts.query.filter(and_(User.id==AllProducts.user_id,AllProducts.name==data["name"])).first()
        if get_product is None:
            return errorMessage("Product doesnt exist")
        name=get_product.name
        price=get_product.price
        description=get_product.description
        product_type=get_product.product_type
        qty=1
        image=get_product.image
        is_added=1
        #user_id=User.is_added
        get_presence=Cart.query.filter(and_(User.id==Cart.user_id,Cart.name==name)).first()
        if get_presence is not None:
            get_presence.qty=get_presence.qty+1
            db.session.commit()
        
        entry=Cart(name=name,price=price,description=description, is_added=1, product_type=product_type, user_id=User.id, qty=qty,image=image)
        db.session.add(entry)
        db.session.commit()
        result = {
            "error": "",
            "status": True
        }
        return jsonify(result)

#Removes each item fom cart
class RemovefromCart(Resource):
    @authenticate_api
    def post(self,**kwargs):
        User = kwargs["user"]
        data=request.get_json()
        db.session.delete(Cart.query.filter(and_(User.id==Cart.user_id,Cart.name==data["name"],Cart.qty==data["qty"])).all())
        db.session.commit()

#Removes all the items from cart
class RemoveAllfromCart(Resource):
    @authenticate_api
    def post(self,**kwargs):
        User = kwargs["user"]
        data=request.get_json()
        db.session.delete(Cart.query.filter((User.id==Cart.user_id)).all())
        db.session.commit()

#Generates bill against a customer
class CustomerCred(Resource):
    @authenticate_api
    def post(self,**kwargs):
        User = kwargs["user"]
        data=request.get_json()
        customer_id=data["customer_id"]
        description=data["description"]
        date_time=datetime.now()
        order_id=Order.id
        user_id=User.id
        get_allproducts=Cart.query.filter(and_(User.id==Cart.user_id)).all()
        res=0
        for product in get_allproducts:
            res+=product.price*product.qty
        total_price=res
        new_order=Order()
        db.session.add(new_order)
        db.session.commit()
        entry=Bill(customer_id=customer_id, order_id=new_order.id, description=description, date_time=date_time, total_price=total_price, user_id=User.id)
        db.session.add(entry)
        db.session.commit()
        result = {
            "customer_id": customer_id,
            "order_id": new_order.id,
            "description": description,
            "total_price": total_price,
            "date_time": date_time
        }
        return jsonify(result) 

#Display all the bills generated till date
class DisplayBills(Resource):
    @authenticate_api
    def get(self,**kwargs):
        User = kwargs["user"]
        get_bills=Bill.query.filter(and_(User.id==Bill.user_id)).all()
        result=[]
        for bill in get_bills:
            result.append ({
            "customer_id": bill.customer_id,
            "order_id": bill.order_id,
            "description": bill.description,
            "total_price": bill.total_price,
            "date_time": product.date_time
        })
        return jsonify(result)

#Display bills against each customer_id
class DisplaybyCustomers(Resource):
    @authenticate_api
    def post(self,**kwargs):
        User = kwargs["user"]
        data=request.get_json()
        get_bills=Bill.query.filter(and_(User.id==Bill.user_id, Bill.customer_id==data["customer_id"] )).all()
        result=[]
        for bill in get_bills:
            result.append ({
            "customer_id": bill.customer_id,
            "order_id": bill.order_id,
            "description": bill.description,
            "total_price": bill.total_price,
            "date_time": product.date_time
        })
        return jsonify(result)

#Displays order on a particular date 
class OrderbyDate(Resource):
    @authenticate_api
    def post(self,**kwargs):
        User = kwargs["user"]
        data=request.get_json()
        get_bills=Bill.query.filter(and_(User.id==Bill.user_id, Bill.date_time==data["date_time"] )).all()
        result=[]
        for bill in get_bills:
            result.append ({
            "customer_id": bill.customer_id,
            "order_id": bill.order_id,
            "description": bill.description,
            "total_price": bill.total_price,
            "date_time": product.date_time
        })
        return jsonify(result)

#Displays orders by date range
class OrderbyDateRange(Resource):
    @authenticate_api
    def post(self,**kwargs):
        User = kwargs["user"]
        data=request.get_json()
        days=data["date_range"]
        dt1=datetime.now() - timedelta(days=days)
        get_bills=Bill.query.filter(and_(User.id==Bill.user_id, Bill.date_time>=dt1 )).all()
        #result={"customer_id": get_bills.customer_id}
        #return jsonify(result)
        result=[]
        for bill in get_bills:
            result.append ({
            "customer_id": bill.customer_id,
            "order_id": bill.order_id,
            "description": bill.description,
            "total_price": bill.total_price,
            "date_time": product.date_time
        })
        return jsonify(result)

#Display the customer list
class DisplayCustomers(Resource):
    @authenticate_api
    def get(self,**kwargs):
        User = kwargs["user"]  
        get_bills=Bill.query.filter(and_(User.id==Bill.user_id)).all()
        customers=[]
        for bill in get_bills:
            if customers.count(bill.customer_id)==0:
                customers.append(bill.customer_id)
        return jsonify(customers)

api.add_resource(Signup, '/v1/api/signup')
api.add_resource(LoginWithPassword, '/v1/api/loginwithpass')
api.add_resource(Logout, '/v1/api/logout')
api.add_resource(LoginWithAccount, '/v1/api/o_login')
api.add_resource(ProfileInfo, '/v1/api/profile')
api.add_resource(UpdateProfile, '/v1/api/updateprofile')
api.add_resource(AddAllProducts, '/v1/api/addallproducts')
api.add_resource(DisplayAllProducts, '/v1/api/displayallproducts')
api.add_resource(AddtoCart, '/v1/api/addtocart')
api.add_resource(DisplayCart, '/v1/api/displaycart')
api.add_resource(RemovefromCart, '/v1/api/removefromcart')
api.add_resource(RemoveAllfromCart, '/v1/api/removeallfromcart')
api.add_resource(CustomerCred, '/v1/api/customercred')
api.add_resource(DisplayBills, '/v1/api/displaybills')
api.add_resource(DisplaybyCustomers, '/v1/api/displaybycustomers')
api.add_resource(OrderbyDate, '/v1/api/orderbydate')
api.add_resource(OrderbyDateRange, '/v1/api/orderbydaterange')
api.add_resource(DisplayCustomers, '/v1/api/displaycustomers')

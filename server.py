from pprint import pprint
from typing import Type
import flask
from flask import Flask, jsonify, request
from flask.views import MethodView
from models import Ads, Session, User
from sqlalchemy.exc import IntegrityError

from schema import CreatesUser, UpdateUser
from flask_login import LoginManager

app = Flask('app')
login_manager = LoginManager(app)


@app.before_request
def before_request():
    session = Session()
    request.session = session


@app.after_request
def after_request(response: flask.Response):
    request.session.close()
    return response


class HttpError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


@app.errorhandler(HttpError)
def error_event(error: HttpError):
    response = jsonify({"error": str(error.message)})
    response.status_code = error.status_code
    return response


def get_ads_id(ads_id: int):
    ads = request.session.query(Ads).get(ads_id)
    pprint(ads)
    if ads is None:
        raise HttpError(status_code=404, message="Ads no found")
    return ads


def add_ads(ads: Ads):
    try:
        if ads.user:
            request.session.add(ads)
            request.session.commit()
        else:
            raise HttpError(status_code=404, message="User noy found")
    except IntegrityError:
        raise HttpError(status_code=409, message="Ads already exists")


def get_user_id(user_id: int):
    user = request.session.query(User).get(user_id)
    if user is None:
        raise HttpError(status_code=404, message="user no found")
    return user


def add_user(user: User):
    try:
        request.session.add(user)
        request.session.commit()
    except IntegrityError:
        raise HttpError(status_code=409, message="user already exists")


def validate_json(json_data: dict, schema_class: Type[CreatesUser] | Type[UpdateUser]):
    try:
        return schema_class(**json_data).dict(exclude_unset=True)
    except ValueError as er:
        error = er.errors()[0]
        error.pop("ctx", None)
        raise HttpError(status_code=400, message=error)


class AdsView(MethodView):
    def get(self, ads_id: int):
        ads = get_ads_id(ads_id)
        user = get_user_id(ads_id)
        return jsonify(ads.dict)

    def post(self):
        ads_data = request.json
        ads = Ads(**ads_data)
        add_ads(ads)
        return jsonify(ads.dict)

    def patch(self, ads_id: int):
        ads_data = request.json
        ads = get_ads_id(ads_id)
        for key, value in ads_data.items():
            setattr(ads, key, value)
        ads_data(ads)
        return jsonify(ads)

    def delete(self, ads_id: int):
        ads = get_ads_id(ads_id)
        request.session.delete(ads)
        request.session.commit()
        return jsonify({"status": "Ads deleted"})


ads_view = AdsView.as_view('ads_view')

app.add_url_rule('/ads/<int:ads_id>',
                 view_func=ads_view,
                 methods=['GET', 'PATCH', 'DELETE'])

app.add_url_rule('/ads/',
                 view_func=ads_view,
                 methods=['POST', ])


class UserView(MethodView):
    def get(self, user_id: int):
        user = get_user_id(user_id)
        return jsonify(user.dict)

    def post(self):
        user_data = validate_json(request.json, CreatesUser)
        user = User(**user_data)
        add_user(user)
        return jsonify(user.dict)

    def patch(self, user_id: int):
        user_data = validate_json(request.json, UpdateUser)
        user = get_user_id(user_id)
        for key, value in user_data.items():
            setattr(user, key, value)
        add_user(user)
        return jsonify(user.dict)

    def delete(self, user_id: int):
        user = get_user_id(user_id)
        request.session.delete(user)
        request.session.commit()
        return jsonify({"status": "user deleted"})


user_view = UserView.as_view('user_view')

app.add_url_rule('/user/<int:user_id>',
                 view_func=user_view,
                 methods=['GET', 'PATCH', 'DELETE'])

app.add_url_rule('/user/',
                 view_func=user_view,
                 methods=['POST', ])

if __name__ == '__main__':
    app.run()

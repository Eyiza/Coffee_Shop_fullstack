import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
from sqlalchemy.exc import IntegrityError
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the database
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES
@app.route('/drinks', methods=['GET'])
def get_drinks():
    try:
        selection = Drink.query.all()
        drinks = [drink.short() for drink in selection]

        return jsonify(
            {
                "success": True,
                "drinks": drinks,
            }
        ), 200
    except:
        abort(500)

@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail():
    try:
        selection = Drink.query.all()
        drinks = [drink.long() for drink in selection]

        return jsonify(
            {
                "success": True,
                "drinks": drinks,
            }
        ), 200
    except:
        abort(403)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drinks():
    body = request.get_json()
    req_title = body.get("title")
    req_recipe = body.get("recipe")

    try:
        drink = Drink(
            title=req_title, 
            recipe=str(req_recipe).replace("\'", "\"")
            )
        drink.insert()
        selection = Drink.query.all()
        drinks = [drink.long() for drink in selection]

        return jsonify(
            {
                "success": True,
                "drinks": drinks,
            }
        ), 200
    except IntegrityError as e:
        return jsonify(
            {
                "success": False,
                "message": "Drink title already exists"
            }
        ), 400

    except:
        abort(405)

@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drinks(id):
    body = request.get_json()
    
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        #print(drink)
        if drink is None:
            abort(404)

        if 'title' in body:
            drink.title = body.get('title')

        if 'recipe' in body:
            drink.recipe = str(body.get('recipe'))

        drink.update()

        selection = Drink.query.all()
        drinks = [drink.long() for drink in selection]

        return jsonify(
            {
                "success": True,
                "drinks": drinks,
            }
        ), 200
    except IntegrityError as e:
        return jsonify(
            {
                "success": False,
                "message": "Drink title already exists"
            }
        ), 400
    except:
        abort(404)


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks/<int:id>", methods=["DELETE"])
@requires_auth('delete:drinks')
def delete_drink(id):
    try:    
        drink = Drink.query.filter(Drink.id == id).one_or_none()

        if drink is None:
            abort(404)

        drink.delete()

        return jsonify(
            {
                "success": True,
                "delete": id,
            }
        ), 200

    except:
        abort(404)


# Error Handling
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422

@app.errorhandler(400)
def bad_request(error):
    return (
        jsonify({
            "success": False, 
            "error": 400, 
            "message": "bad request"
        }), 
        400,
    )

@app.errorhandler(405)
def method_not_allowed(error):
    return (
        jsonify({
            "success": False, 
            "error": 405, 
            "message": "method not allowed"
        }),
        405,
    )

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "Unauthorized request"
    }), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": "Forbidden request"
    }), 403


@app.errorhandler(404)
def not_found(error):
    return (
        jsonify({
            "success": False, 
            "error": 404, 
            "message": "Drink id provided does not exist"
        }), 404
    )
@app.errorhandler(500)
def internal_server_error(error):
    return (
        jsonify({
            "success": False, 
            "error": 500, 
            "message": "Internal server error"
        }),
        500,
    )

@app.errorhandler(AuthError)
def handle_exception(e):
    print(e)
    if e.error['code'] == 'authorization_header_missing':
        return (
            jsonify({
                "success": False, 
                'code': 'authorization_header_missing',
            'description': 'Authorization header is expected.'
            }), 401
        )
    elif e.error['code'] == 'invalid_header':
        if e.error['description'] == 'Authorization header must start with "Bearer".':
            return (
                jsonify({
                    "success": False, 
                    "code": 'invalid_header',
                    "description": 'Authorization header must start with "Bearer".'
                }), 401
            )
        elif e.error['description'] == 'Token not found.':
            return (
                jsonify({
                    "success": False, 
                    "code": 'invalid_header',
                    "description": 'Token not found.'
                }), 401
            )
        elif e.error['description'] == 'Authorization header must be bearer token.':
            return (
                jsonify({
                    "success": False, 
                    "code": 'invalid_header',
                    "description": 'Authorization header must be bearer token.'
                }), 401
            )
        elif e.error['description'] == 'Authorization malformed.':
            return (
                jsonify({
                    "success": False, 
                    "code": 'invalid_header',
                    "description": 'Authorization malformed.'
                }), 401
            )
        elif e.error['description'] == 'Unable to parse authentication token.':
            return (
                jsonify({
                    "success": False, 
                    "code": 'invalid_header',
                    "description": 'Unable to parse authentication token.'
                }), 401
            )
        elif e.error['description'] == 'Unable to find the appropriate key.':
            return (
                jsonify({
                    "success": False, 
                    "code": 'invalid_header',
                    "description": 'Unable to find the appropriate key.'
                }), 401
            )
    elif e.error['code'] == 'invalid_claims':
        if e.error['description'] == 'Permissions not included in JWT.':
            return (
                jsonify({
                    "success": False, 
                    "code": 'invalid_claims',
                    "description": 'Permissions not included in JWT.'
                }), 400
            )
        elif e.error['description'] == 'Incorrect claims. Please, check the audience and issuer.':
            return (
                jsonify({
                    "success": False, 
                    "code": 'invalid_claims',
                    "description": 'Incorrect claims. Please, check the audience and issuer.'
                }), 401
            )
    elif e.error['code'] == 'unauthorized':
        return (
            jsonify({
                "success": False, 
                "code": 'unauthorized',
                "description": 'Permission not found.'
            }), 403
        )
    elif e.error['code'] == 'token_expired':
        return (
            jsonify({
                "success": False, 
                "code": 'token_expired',
                "description": 'Token expired.'
            }), 401
    )


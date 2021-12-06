from flask import Flask, render_template, make_response, jsonify, request
from flask_pymongo import PyMongo
from pymongo.errors import DuplicateKeyError, OperationFailure
from bson.objectid import ObjectId
from bson.errors import InvalidId
import datetime
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()



channel.queue_declare(queue='messages_queue')

app = Flask(__name__)
app.config['MONGO_URI']= 'mongodb+srv://iris:grupo1b@cluster0.qwb35.mongodb.net/iris_messages_db?retryWrites=true&w=majority'
mongo = PyMongo(app)

@app.errorhandler(404)
def resource_not_found(e):
    """
    An error-handler to ensure that 404 errors are returned as JSON.
    """
    return jsonify(error=str(e)), 404


@app.errorhandler(DuplicateKeyError)
def resource_not_found(e):
    """
    An error-handler to ensure that MongoDB duplicate key errors are returned as JSON.
    """
    return jsonify(error=f"Duplicate key error."), 400


@app.route('/sendmessage', methods=['POST'])
def send_message():
    #Receiving data
    print(request.json)
    sender = request.json['sender']
    receiver = request.json['receiver']
    content = request.json['content']
    time_sent = datetime.datetime.now()
    if(sender and receiver and content):
        id = mongo.db.Message.insert_one(
            {'sender': sender, 
            'receiver': receiver,
            'content': content,
            'time_sent': time_sent           
            }
        )
        response = {
            'id':str(id),
            'sender': sender,
            'receiver': receiver,
            'content': content,
            'time_sent': time_sent
        }
        return response

@app.route('/getmessage/<string:user>', methods=['GET'])
def get_message(user):
    cur1=mongo.db.Message.find({"receiver":user})
    res={"Messages": []}
    for doc in cur1:
        time_received = datetime.datetime.now()
        try:
            doc['time_received']
        except KeyError: 
            update = mongo.db.Message.update_one(
            { "_id": doc['_id'] },
            { "$set": { "time_received": time_received} })

    cur2=mongo.db.Message.find({"receiver":user})
    res={"Messages": []}
    for doc in cur2:
        channel.basic_publish(exchange='',
                      routing_key='messages_queue',
                      body=doc['content'])
        print(" [x] Sent" +doc['content'])
        res["Messages"].append( [str(doc['_id']), doc['content'], doc['sender'], doc['time_sent'], doc['time_received']])
    connection.close()
    return res




@app.route('/message/<string:id>', methods=['DELETE'])
def delete_message(id):
    res = mongo.db.Message.delete_one( { "_id": ObjectId(id) } )
    print(res)
    return "Deleted message "+id

@app.route('/updateseen/<id>', methods=['PUT'])
def update_message(id): 
    time_seen= datetime.datetime.now()
    update = mongo.db.Message.update_one(
    { "_id": ObjectId(id) },
    { "$set": { "time_seen": time_seen} })
    return "Updated message"+id

PORT = 8085
HOST = '0.0.0.0'

if __name__=="__main__":
    print("Server running in port %s"%(PORT))
    app.run(host=HOST, port=PORT)
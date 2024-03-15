from pymongo import MongoClient
import random

# Connect to MongoDB
mongo_uri = "mongodb+srv://loki_user:loki_password@clmdemo.1yw93ku.mongodb.net/?retryWrites=true&w=majority&appName=Clmdemo"
client = MongoClient(mongo_uri)
db = client['CLMDigiSignDB']

# Function to generate the next random number
def generate_next_number():
    last_document = db.document_id_seq.find_one({}, sort=[('_id', -1)])  # Get the last document based on _id
    if last_document:
        last_number = last_document.get('number')
        next_number = random.randint(last_number + 1, last_number + 100)  # Generate the next number in a range
        db.document_id_seq.insert()
    else:
        next_number = random.randint(1, 100)  # Generate a random number if no previous number exists
    return next_number

    # # Generate a sequence of random numbers
    # sequence_length = 10
    # random_sequence = [generate_next_number() for _ in range(sequence_length)]

# Store the generated sequence in the database
# documents = [{"number": num} for num in random_sequence]
# db.document_id_seq.insert_many(documents)

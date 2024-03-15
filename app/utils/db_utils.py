def get_next_sequence(db, sequence_name):
    return db.counters.find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"seq": 1}},
        return_document=True
    ).get('seq')

# import logging

# # Configure logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# def get_next_sequence(db, sequence_name):
#     try:
#         result = db.counters.find_one_and_update(
#             {"_id": sequence_name},
#             {"$inc": {"seq": 1}},
#             return_document=True
#         )

#         logger.debug("Sequence document: %s", result)  # Log the sequence document
#         if result:
#             seq_value = result.get('seq')
#             logger.debug("Next sequence value: %d", seq_value)  # Log the extracted sequence value
#             return seq_value
#         else:
#             raise Exception("Sequence not found")
#     except Exception as e:
#         logger.exception("Error occurred while getting next sequence: %s", e)
#         raise  # Re-raise the exception for higher-level handling

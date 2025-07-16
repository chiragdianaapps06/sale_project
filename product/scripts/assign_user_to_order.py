from ordering.logger import get_logger
from ordering.models import Order
from django.contrib.auth import get_user_model
import random

# Initilizing logger 
logger = get_logger("csv_import_logger")

BATCH_SIZE = 10000
# Get user Model
User = get_user_model()


def run(batch_size = BATCH_SIZE):
    '''
      Assigns a random non-superuser agent to each Order in the database.
    '''

    try:
        users = list(User.objects.filter(is_superuser = False))  # fetch all user except super-user

        if not users:
            logger.info("user not found.")

        order = Order.objects.all()  # fetch all order

        order_to_update = []

        # Iterating over order using .Iterator()

        for i, order in enumerate(order.iterator(),start=1):
            order.agent = random.choice(users)

            order_to_update.append(order)

            # bulk update when a batch is full

            if i%batch_size ==0:
                Order.objects.bulk_update(order_to_update, ['agent'], batch_size=BATCH_SIZE)

                logger.info(f"update batch upto {i}")

                order_to_update = []

        # bult update for final batch
        if order_to_update:
            Order.objects.bulk_update(order_to_update, ['agent'], batch_size=BATCH_SIZE)
            
            logger.info("update final batch.")
            order_to_update = []

        logger.info(" All orders have been assigned to random users.")
    except Exception as e:
        logger.critical(f'Script fail due to unexpected error.{e}')



if __name__ == '__main__':
    run()

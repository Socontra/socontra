# Socontra template for the 'allocate' protcol, suitable for automated agent-to-agent non-commercial transactions: task allocation.
# Protocol for the supplier of services.

import random

from socontra.socontra import Socontra, Message, Protocol

# Create a Socontra Client for the agent.
protocol = Protocol()
socontra: Socontra = protocol.socontra
def route(*args):
    def inner_decorator(f):
        protocol.route_map[(args)] = f
        return f
    return inner_decorator



# ----- SOCONTRA SERVICES PROTOCOL: 'allocate' - allocation of a task to agents  -------------------------------------

@route('new_task_request', 'service', 'allocate', 'supplier')  
# -> response: socontra.reject_task(), socontra.submit_offer(), or NoComms and end protocol (task will timeout by received_message.invite_offer_timeout)
def new_task_request(agent_name: str, received_message: Message):
    # The Socontra standard allocate protocol.
    # Supplier agent
    # The supplier receives a new task request to be fulfilled by the consumer. 

    # Agent response
    print(f'\nNew request to fulfill task from {received_message.sender_name}. The task is {received_message.task}\n')

    # Conduct a search if the supplier agent is able to fulfill the task. Get the top search result.
    offer = service_or_product_search(received_message.task)

    if offer is not None:
        # Search results found a suitable service or product that can fulfill the task. Reserve (commit to) and return the offer.

        # Reserve, commit to or secure the service, product or resources needed to complete and deliver the offer.
        # We will use terminology 'add item to cart' (ready for acceptance/purchase) to relate to real world commercial transactions. 
        # However, reservation could be booking a table or a calendar slot for a meeting, or just agreeing to execute 
        # an agent computational task for another agent, etc etc.
        timeout=5
        add_item_to_cart(offer, timeout)
        
        # Submit the offer to the consumer.
        socontra.submit_offer(agent_name, offer=offer, message_responding_to=received_message, offer_timeout=timeout)
    else:
        # No suitable offers. Close the dialogue.
        socontra.close_dialogue(agent_name, received_message)


@route('accept_offer', 'service', 'allocate', 'supplier')  
# -> response: socontra.request_message() (request more info to complete order) or socontra.cancel() to cancel the order or 
#               socontra.order_complete() if successfully completed and delivered or socontra.order_failed()
def accept_offer_supplier(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard allocate protocol.
    # Supplier agent
    # The consumer has 'accepted the offer' to fulfill the task for the consumer.
    # This is like 'purchase item cart' in online stores.
    # The offer has now been purchased, i.e. is a mutually binding contract between the consumer and supplier.
    # Hence, the offer now becomes an 'order' for the supplier to execute and deliver to fulfill the consumer's task.

    # Protocol validation. Messages are only valid if the previous message in the dialogue (message_responding_to) was 'offer'.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['offer']):
        return
    
    # To support protocol control/logic, we can 'close messages' which are no longer valid as we progress through the protocol.
    # We can also socontra.close_agents() if we want to stop a dialogue with a specific agent.
    socontra.close_message(agent_name, close_message_type=['accept_offer', 'reject_offer', 'task_withdrawn'], message_responding_to=received_message)
    
    # Agent response
    print(f'\n{agent_name} offer was accepted by agent {received_message.sender_name}! The (purchase) order is {received_message.order}\n')

    # The accepted offer is now an (purchase) 'order'.
    # Commence executing the order and notify the consumer agent when it is complete, and then close the dialogue/transaction.
    execute_order(agent_name, received_message)


@route('reject_offer', 'service', 'allocate', 'supplier')  
# -> response: N/A, dialogue/transaction end
def reject_offer_supplier(agent_name: str, received_message: Message, message_responding_to: Message):    
    # The Socontra standard allocate protocol.
    # Supplier agent
    # The consumer 'rejected the offer' to fulfill the task for the consumer.

    # Protocol validation. Messages are only valid if the previous message in the dialogue (message_responding_to) was 'offer'.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['offer']):
        return
    
    # Agent response
    print(f'\n{agent_name} had its offer rejected to fulfill task {received_message.task} by {received_message.sender_name}. The reason is {received_message.message}\n')

    # Release the resources/protict/service, i.e. remove item from the cart and make it available to other agents.
    remove_item_from_cart(received_message)

    # End the dialogue/transaction.
    socontra.close_dialogue(agent_name, received_message)


@route('request_message', 'service', 'allocate', 'supplier')  
# -> response: NoComms (until order complete), socontra.request_message() (more info exchanges), 
#               socontra.cancel_order(), socontra.order_complete(), socontra.order_failed()
def request_message_supplier(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard protocol.
    # Supplier agent
    # Consumer sent a message to the supplier
    # These messages can be used for sending messages between consumer and supplier necessary to complete the order 
    # in order to fulfill/achieve the task.

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['offer', 'request_message']):
        return

    # Agent response
    print('\n', received_message.sender_name, ' sent a message relating to the order, which is ', received_message.message, '\n')
 
    # Return the message for the supplier order execution/delivery function.
    socontra.agent_return(agent_name, request_message_supplier, received_message=received_message)


@route('cancel_order', 'service', 'allocate', 'supplier')  
# -> response: protocol/dialogue end.
def cancel_order_supplier(agent_name: str, received_message: Message, message_responding_to: Message):    
    # The Socontra standard allocate protocol.
    # Supplier agent
    # The consumer canceled the order that was agreed to or purchased.

    # Protocol validation.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['offer', 'request_message']):
        return
    
    # Agent response
    print('\nOrder was canceled by the consumer ', received_message.sender_name, ' which was ', received_message.order, '. The reason/message is ', received_message.message, '\n')

    # End the dialogue/transaction.
    socontra.close_dialogue(agent_name, received_message)


@route('confirm_success', 'service', 'allocate', 'supplier')  
# -> response: N/A - successful exit
def order_complete_confirm_success(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard allocation protocol.
    # Supplier agent
    # The consumer has provided a 'sign-off' that the completed/delivered order was in fact completed satisfactorily.   

    # Protocol validation.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['order_complete']):
        return
    
    # Agent response
    print('\nSign-off for completed/delivered order has been received by the consumer: ', received_message.sender_name, '. Feedback is:', received_message.message, '\n')

    # Return the message so that the supplier order orchestrator can handle it.
    socontra.agent_return(agent_name, order_complete_confirm_success, received_message=received_message)


@route('confirm_fail', 'service', 'allocate', 'supplier')  
# -> response: N/A - unsuccessful exit
def order_complete_confirm_fail(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard allocation protocol.
    # Supplier agent
    # This supplier has been notified that the consumer did not provided a 'sign-off' for the completed/delivered order, because it was 
    # not completed satisfactorily.    

    # Protocol validation.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['order_complete']):
        return
    
    # Agent response
    print('\nConsumer ', received_message.sender_name, ' did not sign-off on the completed/delivered order. Feedback is:', received_message.message, '\n')

    # Return the message so that the supplier order orchestrator can handle it.
    socontra.agent_return(agent_name, order_complete_confirm_success, received_message=received_message)


@route('task_withdrawn', 'service', 'allocate', 'supplier')  
# -> response: N/A - exit - transaction/dialogue complete.
def task_withdrawn_supplier(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard allocation protocol.
    # Supplier agent
    # This supplier has been notified that the consumer has withdrawn the task request. This concludes the transaction/dialogue.

    # Protocol validation.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['offer']):
        return
    
    # Agent response
    print('\nConsumer ', received_message.sender_name, ' has withdrawn the task request. Message is:', received_message.message, '\n')

    # Execute any final wrap up tasks.

    # End the dialogue/transaction.
    socontra.close_dialogue(agent_name, received_message)


# SUPPLIER FUNCTIONS FOR ALLOCATE PROTOCOL


def service_or_product_search(task):
    # Run a search on the database for services, products or resources that can to fulfill the task.

    # For this demo, we assume we found a service (method) to add numbers. The 'cost' of completing the offer
    # is a random number from 1 to 10.
    return {
        'method': 'Will use the + operator',
        'cost': random.randint(1, 10)
    }

def add_item_to_cart(offer, timeout):
    # Reserve, commit to or secure the service, product or resources needed to complete and deliver the offer.
    # Release the service, product or resources (remove item from cart) if no response by timeout.

    # In this example, addition of two numbers do not need reservation of any particular computational or physical resource.
    pass

def remove_item_from_cart(rejected_offer):
    # Remove/release the item (service, product or resources) from cart.
    pass


def execute_order(agent_name, order_message):
    # To execute the order, the agent needs to know what numbers are needed to add.
    # Send a message to the agent asking for the numbers.
    socontra.request_message(agent_name, message='What are the two numbers you want me to add.', message_responding_to=order_message, recipient_type='consumer')

    # Wait for the agent to respond back with the required information.
    agent_instructions_message = socontra.expect(agent_name, request_message_supplier)
    agent_instructions = agent_instructions_message['received_message']

    # Now add the two numbers.
    sum_order = agent_instructions.message['a'] + agent_instructions.message['b']

    # Now notify the consumer agent that the order has been completed and delivered. 
    # In this example, the message contains the result.
    socontra.order_complete(agent_name, message={'result': sum_order}, message_responding_to=order_message)

    # Wait for order complete confirmation.
    message_type, order_confirmation_returned = socontra.expect_multiple(agent_name, [order_complete_confirm_success, order_complete_confirm_fail])
    order_confirmation = order_confirmation_returned['received_message']

    if message_type == 'order_complete_confirm_success':
        # Perform any finalization or wrap up tasks and complete the transaction
        print('Customer confirmed order with message ', order_confirmation.message)
        pass
    else:
        # There was a problem with the completion/delivery of the order. Resolve issues here.
        print('Customer unhappy with order, message is ', order_confirmation.message)
        pass

    # End the dialogue for this process and return.
    socontra.close_dialogue(agent_name, order_message)
    





   
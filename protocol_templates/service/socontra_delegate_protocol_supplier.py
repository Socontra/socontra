# Socontra template for the 'delegate' protocol, suitable for simplified automated agent-to-agent task delegation.
# Protocol for the supplier of services.

import time

from socontra.socontra import Socontra, Message, Protocol

# Create a Socontra Client for the agent.
protocol = Protocol()
socontra: Socontra = protocol.socontra
def route(*args):
    def inner_decorator(f):
        protocol.route_map[(args)] = f
        return f
    return inner_decorator


# ----- SOCONTRA PROTOCOL: 'delegate'   -------------------------------------


@route('new_task_request', 'service', 'delegate', 'supplier')  
# -> response:  socontra.reject_offer or socontra.accept_offer() + (optional) socontra.request_message (info to fulfill order)
def new_task_request(agent_name: str, received_message: Message):
    # The Socontra standard delegation protocol.
    # Supplier agent
    # The supplier receives a new task request to be fulfilled by the consumer. 
    # For delegation, task is effectively an 'offer' to be accepted/rejected by the supplier agent. Not suited for typical transactions between 
    # agents that are 'autonomous' or conducting commercial transactions.
    
    # Agent response
    print('\nNew request to fulfill task from', received_message.sender_name, '. The task is ', received_message.task, '\n')

    # Responses to the request - accept or reject. 
    # REMEMBER to include recipient (only for delegation) as typical roles reversed for accepting an offer (consumer, not supplier).
    # socontra.reject_offer(agent_name, message_responding_to=received_message, recipient_type='consumer')     # Then socontra.protocol_end(agent_name, received_message) to end the dialogue/transaction.
    socontra.accept_offer(agent_name, message_responding_to=received_message, recipient_type='consumer')
    
    time.sleep(2)
    
    # The accepted offer is now an (purchase) 'order'.
    # Commence executing the order (or relevant function) here if response above was socontra.accept_offer(agent_name, received_message).

    # Execution may involve messages to the consumer to fulfill the order.
    socontra.request_message(agent_name, message='Where would you like us to leave the package with the numbers.', message_responding_to=received_message, recipient_type='consumer')

    # Completion of the delivery involves response confirming completion and the completion status, or canceling the order.
    # In this demo, we do this after exchange of messages with socontra.request_message() above.

    # socontra.cancel_order(agent_name, message='My calculator broke.', message_responding_to=received_message, recipient_type='consumer')
    # socontra.order_complete(agent_name, message='Order complete, left at your front door.', message_responding_to=received_message)
    # socontra.order_failed(agent_name, message='Could not open your front gate to leave the package at front door.', message_responding_to=received_message)

    # End the dialogue after order is complete or canceled.
    # Then socontra.close_dialogue(agent_name, received_message) to end the dialogue/transaction.


@route('request_message', 'service', 'delegate', 'supplier')  # -> response: NoComms (until order complete), socontra.request_message() (info to complete order), socontra.cancel_order(), socontra.order_complete(), socontra.order_failed()
def request_message_supplier(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard protocol.
    # Supplier agent
    # Consumer sent a message to the supplier
    # These messages can be used for sending messages between consumer and supplier necessary to complete the order in order to fulfill/achieve the task.

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['accept_offer', 'request_message']):
        return

    # Agent response
    print('\n', received_message.sender_name, ' sent a message relating to the order, which is ', received_message.message, '\n')
 
    # Execution may involve additional messages to the consumer to fulfill the order.
    # socontra.request_message(agent_name, message='Delivery instructions acknowledged.', message_responding_to=received_message, recipient_type='consumer')
    
    # Completion of the delivery involves response confirming completion and the completion status, or canceling the order.
    # socontra.cancel_order(agent_name, message='My calculator broke.', message_responding_to=received_message, recipient_type='consumer')
    socontra.order_complete(agent_name, message='Order complete, left at your front door.', message_responding_to=received_message)
    # socontra.order_failed(agent_name, message='Could not open your front gate to leave the package at front door.', message_responding_to=received_message)
    
    # Then socontra.close_dialogue(agent_name, received_message) for all responses but socontra.request_message()


@route('cancel_order', 'service', 'delegate', 'supplier')  # -> response: protocol/dialogue end.
def cancel_order_supplier(agent_name: str, received_message: Message, message_responding_to: Message):    
    # The Socontra standard delegation protocol.
    # Supplier agent
    # The consumer canceled the order that was agreed to or purchased.

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['accept_offer', 'request_message']):
        return
    
    # Agent response
    print('\nOrder was canceled by the consumer ', received_message.sender_name, ' which was ', received_message.order, '. The reason/message is ', received_message.message, '\n')

    # End the dialogue/transaction.
    socontra.close_dialogue(agent_name, received_message)



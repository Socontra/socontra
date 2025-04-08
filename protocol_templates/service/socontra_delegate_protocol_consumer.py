# Socontra template for the 'delegate' protocol, suitable for simplified automated agent-to-agent task delegation.
# Protocol for the consumer of services.

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


@route('accept_offer', 'service', 'delegate', 'consumer')  
# -> response: socontra.request_message() (info to complete order) or socontra.cancel() or NoComms (wait for completion message)
def accept_offer_consumer(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard delegation protocol.
    # Consumer agent
    # The supplier has 'accepted the offer' to fulfill the task for the consumer.
    # This is like 'purchase item cart' in online stores.
    # The offer has now been purchased, i.e. is a mutually binding contract between the consumer and supplier.
    # Hence, the offer now becomes an 'order' for the supplier to execute and deliver to fulfill the consumer's task.

    # Protocol validation.
    # Note: Specifying 'new_task_request' as a valid prior protocol message is what allows the supplier to accept a task and not an offer
    # to create an order for execution.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['new_task_request']):
        return
    
    # To support protocol control/logic, we can 'close messages' which are no longer valid as we progress through the protocol.
    # We can also socontra.close_agents() if we want to stop a dialogue with a specific agent.
    socontra.close_message(agent_name, close_message_type=['accept_offer', 'reject_offer'], message_responding_to=received_message)
    
    # Agent response
    print('\nOffer accepted to fulfill task by ', received_message.sender_name, '. The (purchase) order is ', received_message.order, '\n')

    # Commence executing any monitoring or tracking of the order, or wait for completion message from the supplier.
    # time.sleep(2)

    # Consumer can cancel the order at anytime.
    # socontra.cancel_order(agent_name, message='Deadline missed.', message_responding_to=received_message, recipient_type='supplier')  # Then socontra.close_dialogue(agent_name, received_message) to end the dialogue/transaction.
    
    # Or the consumer can exchange info to the supplier to help it complete the order.
    # socontra.request_message(agent_name, message='Leave the package by the front door.', message_responding_to=received_message, recipient_type='supplier')

    # Or exit here and wait for the completion message.


@route('reject_offer', 'service', 'delegate', 'consumer')  
# -> response: protocol/dialogue end -> start new protocol/dialogue to find an alternative agent to fulfill task.
def reject_offer_consumer(agent_name: str, received_message: Message, message_responding_to: Message):    
    # The Socontra standard delegation protocol.
    # Consumer agent
    # The supplier 'rejected the offer' to fulfill the task for the consumer.

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['new_task_request']):
        return
    
    # Agent response
    print('\nOffer rejected to fulfill task ', received_message.task, ' by ', received_message.sender_name, '. The reason/message is ', received_message.message, '\n')

    # End the dialogue/transaction. Possibly try again with a different agent (start a new dialogue/protocol).
    socontra.close_dialogue(agent_name, received_message)

    # Initiate replanning options here.


@route('request_message', 'service', 'delegate', 'consumer')  
# -> response: NoComms (wait until order complete), socontra.request_message() (info to complete order) or socontra.cancel_order()
def request_message_consumer(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard delegation protocol.
    # Consumer agent
    # Supplier sent a message to the supplier.
    # These messages can be used for sending messages between consumer and supplier necessary to complete the order in order to fulfill/achieve the task.

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['new_task_request', 'request_message']):
        return

    # Agent response
    print('\n', received_message.sender_name, ' sent a message relating to the order, which is ', received_message.message, '\n')
    
    # Possible messages at this stage:
    # socontra.cancel_order(agent_name, message='Deadline missed.', message_responding_to=received_message, recipient_type='supplier') # Then socontra.close_dialogue(agent_name, received_message) to end the dialogue/transaction.
    
    socontra.request_message(agent_name, message='Leave the package by the front door.', message_responding_to=received_message, recipient_type='supplier')


@route('cancel_order', 'service', 'delegate', 'consumer')  
# -> response: unsuccessful exit -> start new protocol/dialogue to find an alternative agent to fulfill task.
def cancel_order_consumer(agent_name: str, received_message: Message, message_responding_to: Message):    
    # The Socontra standard delegation protocol.
    # Consumer agent
    # The supplier canceled the order that was agreed to or purchased.

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['new_task_request', 'request_message']):
        return
    
    # Agent response
    print('\nOrder was canceled by the supplier ', received_message.sender_name, ' which was ', received_message.order, '. The reason/message is ', received_message.message, '\n')

    # End the dialogue/transaction.
    socontra.close_dialogue(agent_name, received_message)

    # Initiate replanning options here.


@route('order_complete', 'service', 'delegate', 'consumer')  
# -> response: N/A - successful exit
def order_complete_consumer(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard delegation protocol.
    # Consumer agent
    # The supplier has completed and/or delivered the order to fulfill the task for the consumer.

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['new_task_request', 'request_message']):
        return
    
    # Agent response
    print('\nOrder to fulfill task has been completed by ', received_message.sender_name, '. The (purchase) order was ', received_message.order, 
          ' and completion message is ', received_message.message, '\n')

    # Execute any finalization or wrap up tasks here.

    # End the dialogue/transaction.
    socontra.close_dialogue(agent_name, received_message)


@route('order_failed', 'service', 'delegate', 'consumer')  
# -> response: unsuccessful exit -> start new protocol/dialogue to find an alternative agent to fulfill task.
def order_failed_consumer(agent_name: str, received_message: Message, message_responding_to: Message):    
    # The Socontra standard delegation protocol.
    # Consumer agent
    # The supplier could not execute or deliver on the order that was agreed to or purchased.

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['new_task_request', 'request_message']):
        return
    
    # Agent response
    print('\nOrder could not be fulfilled by the supplier ', received_message.sender_name, ' which was ', received_message.order, '. The reason/message is ', received_message.message, '\n')

    # End the dialogue/transaction.
    socontra.close_dialogue(agent_name, received_message)

    # Initiate replanning options here.


# Socontra template for the 'transact' protocol, suitable for automated agent-to-agent commercial transactions.
# Protocol for the supplier of services.

import time
import random

from bisect import insort

from socontra.socontra import Socontra, Message, Protocol

# Create a Socontra Client for the agent.
protocol = Protocol()
socontra:Socontra = protocol.socontra
def route(*args):
    def inner_decorator(f):
        protocol.route_map[(args)] = f
        return f
    return inner_decorator


# ----- SOCONTRA PROTOCOL: 'transact' - allocation of a task to agents  -------------------------------------

@route('new_task_request', 'service', 'transact', 'supplier')  
# -> response: socontra.reject_task(), socontra.submit_proposal(), or NoComms and end protocol (task will timeout by received_message.proposal_timeout)
def new_task_request(agent_name: str, received_message: Message):
    # The Socontra standard transact protocol.
    # Supplier agent
    # The supplier receives a new task request to be fulfilled by the consumer.
    # This is equilavent to a 'product search' in online stores.
    
    print(f'\nNew request to fulfill task from {received_message.sender_name}. The task is {received_message.task} requires a response by {socontra.get_deadline(received_message.proposal_timeout)}\n')
  
    # Conduct a search if the supplier agent is able to fulfill the task. Get the top search result.
    proposal = service_or_product_search(received_message.task)

    if proposal is not None:
        # Search results found a suitable service or product that can fulfill the task.
        # Return the proposal to the consumer (one per message). 
        # The supplier agent is not committed to the proposal at this stage - just info exchange.
        # Therefore, no need for the consumer to reject the proposal if not suitable (that is optional).
        # If the proposal is suitable, the consumer will send an 'invite_offer' (i.e. 'add item to cart') 
        # message for the supplier to submit the proposal as a formal offer, which is binding.
        socontra.submit_proposal(agent_name, proposal=proposal, message_responding_to=received_message)
    else:
        # Reject the task (is optional).
        socontra.reject_task(agent_name, message_responding_to=received_message, message='I only multiply. I am unable to add or turn left.')
        socontra.close_dialogue(agent_name, received_message)


@route('reject_proposal', 'service', 'transact', 'supplier')  
# -> response: end the dialogue/transaction with the consumer for the specific task. 
#    Optionally, the supplier could submit another proposal, if the protocol and timeout expiry allows.
def reject_proposal_supplier(agent_name: str, received_message: Message, message_responding_to: Message):    
    # The Socontra standard transact protocol.
    # Supplier agent
    # The consumer 'rejected the proposal' submitted to the supplier.
    # This message is optional, and can be used to inform the supplier that the offer was not suitiable and to submit another 
    # if time allows (i.e. reject_proposal implies return more search results).

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['proposal']):
        return
    
    print('\nProposal rejected for task ', received_message.task, ' by ', received_message.sender_name, '. The reason/message is ', received_message.message, '\n')

    # End dialogue.
    socontra.close_dialogue(agent_name, received_message)


@route('invite_offer', 'service', 'transact', 'supplier')  
# -> response: socontra.submit_offer() (with an optional socontra.revoke_offer() following submission, if required), 
#              socontra.reject_invite_offer(), or NoComms (invite offer will timeout by received_message.invite_offer_timeout)
def receive_invite_offer(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard transact protocol.
    # Supplier agent
    # The consumer has sent an invite offer request asking the supplier to submit the proposal as a formal binding offer.
    # This is equivalent to the consumer requesting that the supplier "add item to cart" in online stores.
    # If the offer is sent via socontra.submit_offer(), that is equivalent to informing the consumer "item was added to cart".

    # Protocol validation.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['proposal']):
        return
    
    print('\nInvite to offer for proposal ', received_message.proposal, ' was received by  ', agent_name, ' from ', received_message.sender_name, ' requires a response by ',
          socontra.get_deadline(received_message.invite_offer_timeout), '\n')
    
    # Reserve, hold, book, commit to or secure the service, product or resources needed to complete and deliver the offer, 
    # and submit the binding/committed offer to the consumer.
    timeout = 5
    offer = add_item_to_cart(received_message, timeout)

    if offer:
        # Submit the offer to the consumer. Assume payment and human authorization for the purchase is required.
        socontra.submit_offer(agent_name, offer=offer, message_responding_to=received_message, 
                              offer_timeout=timeout, payment_required = True, human_authorization_required = True)

        # If the situation changes, can revoke the offer ('remove item from cart) with the below commands.
        # Note need to pass in the response message returned from the Socontra Network from command socontra.submit_offer().
        # socontra.revoke_offer(agent_name, offer=offer, message_responding_to=received_message)
        # remove_item_from_cart(received_message.offer)
    else:
        # Offer is no longer available.
        # Out of courtesy, can reject the invite offer so that the consumer does not have to wait for expiry to select another proposal.
        socontra.reject_invite_offer(agent_name, message_responding_to=received_message)
        
        # End dialogue.
        socontra.close_dialogue(agent_name, received_message)


@route('accept_offer', 'service', 'transact', 'supplier')  
# -> response:  If payment for services required: socontra.payment_confirmed() or socontra.payment_denied()
#               Else: socontra.request_message() (info exchange to complete order) or socontra.cancel() (to cancel the order) or 
#                     order completion/delivery messages: socontra.order_complete() or socontra.order_failed()
def accept_offer_supplier(agent_name: str, received_message: Message, message_responding_to: Message, payment: str | dict, human_authorization: bool | str | dict):
    # The Socontra standard transact protocol.
    # Supplier agent
    # The consumer has 'accepted the offer' for the supplier to fulfill the task.
    # This message is equilavent to 'purchase item in cart' with online stores.
    # If there is no payment, the offer now becomes an 'order' for execution by the supplier (a mutually binding contract).
    # If payment is required, the offer is not yet a mutually binding 'order' until supplier responds with a 
    # socontra.payment_confirmed() message.

    # Protocol validation.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['offer', 'payment_error']):
        return
    
    print('\nOffer accepted to fulfill task by ', received_message.sender_name, '. The (purchase) order is ', received_message.order, '\n')

    # Check if payment is required for the order.
    if received_message.payment_required:

        # In case of payment errors, set a timeout for the consumer agent to respond with another accept_offer to resolve the issue.
        timeout = 5

        # Check human authorization.
        human_authorization_ok = check_human_authorization(received_message, human_authorization)

        if not human_authorization_ok:
            # Inform the consumer agent that the order payment needs human authorization.
            socontra.payment_error(agent_name, message = 'Human authorization failed. Please try again.', offer_timeout=timeout, message_responding_to=received_message)
            return

        # Now process payment.
        payment_response = process_payment_supplier(received_message.offer, payment)

        if payment_response == 'confirmed':
            # Payment processed. Inform the consumer and the order is now in place.
            socontra.payment_confirmed(agent_name, message = 'purchase order details. Invoice #1. Add two numbers', message_responding_to=received_message)
        else:
            # Error with payment. Assume error message in payment_response variable. Inform the consumer agent.
            socontra.payment_error(agent_name, message = payment_response, offer_timeout=timeout, message_responding_to=received_message)
            return
    
    # To support protocol control/logic, we can 'close messages' which are no longer valid as we progress through the protocol.
    # We can also socontra.close_agents() if we want to stop a dialogue with a specific agent.
    # The order is now in place. Close protocol messages that are no longer relevant.
    socontra.close_message(agent_name, close_message_type=['invite_offer', 'reject_proposal', 'task_withdrawn', 'reject_offer', 'accept_offer'], message_responding_to=received_message)

    # Complete and deliver the order, and send completion messages when done.
    complete_and_deliver_order(agent_name, received_message)


@route('reject_offer', 'service', 'transact', 'supplier')  
# -> response: end dialogue/transaction, or (optionally) submit an alternative proposal
def reject_offer_supplier(agent_name: str, received_message: Message, message_responding_to: Message):    
    # The Socontra standard transact protocol.
    # Supplier agent
    # The consumer 'rejected the offer' to fulfill the task for the consumer.

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['offer']):
        return
    
    # Agent response
    print('\nOffer rejected to fulfill task ', received_message.task, ' by ', received_message.sender_name, '. The reason/message is ', received_message.message, '\n')

    # Remove item from cart: release the resource, service or product to make it available for other agents.
    remove_item_from_cart(received_message.offer)

    # End the dialogue/transaction.
    socontra.close_dialogue(agent_name, received_message)


@route('request_message', 'service', 'transact', 'supplier')  
# -> response: socontra.request_message() (reply to message), socontra.cancel_order(), socontra.order_complete(), socontra.order_failed()
def request_message_supplier(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard protocol.
    # Supplier agent
    # Consumer sent a message to the supplier
    # These messages can be used for sending messages between consumer and supplier necessary to complete the order in order to fulfill/achieve the task.

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['offer', 'payment_confirmed', 'request_message']):
        return

    print('\n', received_message.sender_name, ' sent a message relating to the order, which is ', received_message.message, '\n')
 
    # Return the response to the supplier function that is executing and delivering the order.
    socontra.agent_return(agent_name, request_message_supplier, received_message=received_message)


@route('cancel_order', 'service', 'transact', 'supplier')  
# -> response: end dialogue/transaction.
def cancel_order_supplier(agent_name: str, received_message: Message, message_responding_to: Message):    
    # The Socontra standard transact protocol.
    # Supplier agent
    # The consumer canceled the order that was agreed to or purchased.

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['offer', 'request_message']):
        return
    
    # Agent response
    print('\nOrder was canceled by the consumer ', received_message.sender_name, ' which was ', received_message.order, '. The reason/message is ', received_message.message, '\n')

    # End the dialogue/transaction.
    socontra.close_dialogue(agent_name, received_message)


@route('confirm_success', 'service', 'transact', 'supplier') 
# -> response: end the dialogue/transaction (successful exit)
def order_complete_confirm_success(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard allocation protocol.
    # Supplier agent
    # The consumer has provided a 'sign-off' that the completed/delivered order was in fact completed satisfactorily.   

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['order_complete']):
        return
    
    # Agent response
    print('\nSign-off for completed/delivered order has been received by the consumer: ', received_message.sender_name, '. Feedback is:', received_message.message, '\n')

    # Send the message back to the main supplier function that is executing and delivering on the order to perform
    # any finialization and wrap up tasks, and close out the dialogue/transaction.
    socontra.agent_return(agent_name, order_complete_confirm_success, received_message=received_message)


@route('confirm_fail', 'service', 'transact', 'supplier') 
# -> response: end the dialogue/transaction (unsuccessful exit)
def order_complete_confirm_fail(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard allocation protocol.
    # Supplier agent
    # This supplier has been notified that the consumer did provided a 'sign-off' for the completed/delivered order, because it was 
    # not completed or delivered satisfactorily.    

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['order_complete']):
        return
    
    print('\nConsumer ', received_message.sender_name, ' did not sign-off on the completed/delivered order. Feedback is:', received_message.message, '\n')

    # Send the message back to the main supplier function that is executing and delivering on the order to perform
    # any order resolution actions, before closing out the dialogue/transaction.
    socontra.agent_return(agent_name, order_complete_confirm_success, received_message=received_message)


@route('task_withdrawn', 'service', 'transact', 'supplier')  
# -> response: end the dialogue/transaction
def task_withdrawn_supplier(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard allocation protocol.
    # Supplier agent
    # This supplier has been notified that the consumer has withdrawn the task request. This concludes the transaction/dialogue.

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['offer']):
        return
    
    print('\nConsumer ', received_message.sender_name, ' has withdrawn the task request. Message is:', received_message.message, '\n')

    # End the dialogue/transaction.
    socontra.close_dialogue(agent_name, received_message)


# SUPPLIER FUNCTIONS FOR TRANSACT PROTOCOL


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

    # In this example, addition of two numbers do not need reservation of any particular computational or physical resource.
    pass
    return offer.proposal  

def remove_item_from_cart(offer):
    # Offer was rejected by the consumer or revoked by the supplier. Remove the item from cart.
    pass
    return True

def process_payment_supplier(received_message, payment):
    # Process the payment for the order.
    pass

    # process_payment_response = 'credit card payment denied'
    process_payment_response = 'confirmed'
    return process_payment_response

def check_human_authorization(received_message, human_authorization):
    # Will check human authorization. Could be a boolean that it was done, or some sort of signature or password that can be authenticated.
    # How this is implemented is up to the developer.
    pass
    return True

def complete_and_deliver_order(agent_name, order_message):
    # To execute the order, the agent needs to know what numbers are needed to add.
    
    # Send a message to the agent asking for the numbers.
    res = socontra.request_message(agent_name, message='What are the two numbers you want me to add.', message_responding_to=order_message, recipient_type='consumer')

    # Wait for the agent to respond back with the required information.
    agent_instructions_message = socontra.expect(agent_name, request_message_supplier)
    agent_instructions = agent_instructions_message['received_message']

    # Execute the task, i.e. add two numbers.
    completion, result = add_two_numbers(agent_instructions.message['a'], agent_instructions.message['b'])

    # Now notify the consumer agent that the order has been completed and delivered. 
    # In this example, the message contains the result.
    if completion == 'successful':
        socontra.order_complete(agent_name, message={'result': result}, message_responding_to=order_message)
    elif completion == 'unsuccessful':
        socontra.order_failed(agent_name, message='Could not add the numbers - they were too large, I can only count to 2.', message_responding_to=order_message)
    elif completion == 'cancel':
        socontra.cancel_order(agent_name, message='Sorry, service out of stock - my agent quit.', message_responding_to=order_message, recipient_type='consumer')

    # Wait for optional signoff from the consumer of the completed and delivered services.
    if completion == 'successful' and order_delivery_signoff():
        # Wait for order complete confirmation.
        message_type, order_confirmation_returned = socontra.expect_multiple(agent_name, [order_complete_confirm_success, order_complete_confirm_fail])
        order_confirmation = order_confirmation_returned['received_message']

        if message_type == 'order_complete_confirm_success':
            # Perform any finalization or wrap up tasks and complete the transaction
            print('Customer confirmed order with message ', order_confirmation.message)
            pass
        else:
            # There was a problem with the completion/delivery of the order. Resolve issues here.
            print('Customer unhappy with order, message is ', order_confirmation.message, ' send a sorry card.')
            pass

    # End the dialogue for this process and return.
    socontra.close_dialogue(agent_name, order_message)

def add_two_numbers(a, b):
    # Will add two numbers, as required by the order.
    return 'successful', a + b

def order_delivery_signoff():
    # Return True if the supplier requires signoff on the completion and delivery of the order.
    return True
